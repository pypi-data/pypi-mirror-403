import asyncio
import io
import os
import tempfile
from typing import AsyncGenerator, Literal

import ibis
import pyarrow as pa
import pyarrow.csv as pacsv
import pyarrow.parquet as pq
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from ibis.common.exceptions import TableNotFound
from pydantic import BaseModel

from planar.data.exceptions import DatasetNotFoundError
from planar.data.utils import (
    get_dataset,
    get_dataset_metadata,
    get_datasets_metadata,
    list_datasets,
    list_schemas,
)
from planar.logging import get_logger
from planar.security.authorization import (
    DatasetAction,
    DatasetResource,
    validate_authorization_for,
)

logger = get_logger(__name__)

# Constants for streaming
BATCH_SIZE = 10000
CHUNK_SIZE = 1024 * 1024  # 1MB chunks


def _read_file_chunk(
    file_path: str, position: int, chunk_size: int
) -> tuple[bytes, int]:
    """
    Read a single chunk from a file at the given position.
    Returns the chunk and the new position, or empty bytes if EOF.
    """
    with open(file_path, "rb") as f:
        f.seek(position)
        chunk = f.read(chunk_size)
        new_position = f.tell()
    return chunk, new_position


async def _iter_file_chunks(
    path: str, chunk_size: int = CHUNK_SIZE
) -> AsyncGenerator[bytes, None]:
    """
    Async generator that streams file contents in chunks without blocking the event loop.
    Cleans up the file afterward.

    Args:
        path: Path to the file to stream
        chunk_size: Size of each chunk in bytes

    Yields:
        Byte chunks of the file content
    """
    try:
        position = 0
        while True:
            # Offload file I/O to thread pool to avoid blocking
            chunk, new_position = await asyncio.to_thread(
                _read_file_chunk, path, position, chunk_size
            )

            if not chunk:
                break

            yield chunk
            position = new_position
    finally:
        try:
            await asyncio.to_thread(os.remove, path)
        except Exception as e:
            logger.warning("failed to remove temp file", path=path, error=str(e))


async def stream_csv(
    table: ibis.Table, batch_size: int = BATCH_SIZE
) -> AsyncGenerator[bytes, None]:
    """
    Stream CSV data from an Ibis table using PyArrow's CSV writer.

    Args:
        table: Ibis table expression to stream
        batch_size: Number of rows to process per batch

    Yields:
        Byte chunks of CSV data
    """
    try:
        row_count = 0
        batches = table.to_pyarrow_batches(chunk_size=batch_size)

        for batch_index, batch in enumerate(batches):
            output = pa.BufferOutputStream()
            table_batch = pa.Table.from_batches([batch])

            await asyncio.to_thread(
                pacsv.write_csv,
                table_batch,
                output,
                write_options=pacsv.WriteOptions(include_header=(batch_index == 0)),
            )

            chunk_bytes = output.getvalue().to_pybytes()
            if chunk_bytes:
                yield chunk_bytes

            row_count += batch.num_rows
            logger.debug(
                "streamed batch",
                rows_processed=row_count,
                batch_rows=batch.num_rows,
                batch_index=batch_index,
            )

    except Exception as exc:
        logger.exception("error streaming csv", error=str(exc))
        raise HTTPException(
            status_code=500,
            detail=f"Error generating CSV: {str(exc)}",
        )


async def stream_parquet(
    table: ibis.Table, batch_size: int = BATCH_SIZE
) -> AsyncGenerator[bytes, None]:
    """
    Uses a temporary file to avoid loading the entire Parquet file into memory.
    Memory usage is bounded to O(batch_size) regardless of dataset size.

    Args:
        table: Ibis table expression to stream
        batch_size: Number of rows to process per batch

    Yields:
        Byte chunks of the parquet file content
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".parquet", delete=False)
    path = tmp.name
    tmp.close()  # Close handle so ParquetWriter can open it

    writer = None
    row_count = 0

    try:
        batches = table.to_pyarrow_batches(chunk_size=batch_size)

        for batch in batches:
            # Initialize writer with schema from first batch (offload to thread pool)
            if writer is None:
                writer = await asyncio.to_thread(
                    pq.ParquetWriter,
                    path,
                    batch.schema,
                    compression="zstd",
                    write_statistics=True,
                )

            # Offload blocking write operation to thread pool
            await asyncio.to_thread(writer.write_batch, batch)

            row_count += batch.num_rows
            logger.debug(
                "wrote parquet batch",
                rows_processed=row_count,
                batch_rows=batch.num_rows,
            )

        # Handle empty datasets - create parquet file with schema but no data
        if writer is None:
            schema = table.schema().to_pyarrow()
            writer = await asyncio.to_thread(
                pq.ParquetWriter,
                path,
                schema,
                compression="zstd",
                write_statistics=True,
            )
            logger.warning("dataset is empty", row_count=0)

        # Close writer to finalize parquet file (writes footer) - offload to thread pool
        await asyncio.to_thread(writer.close)

        # Stream the file in chunks asynchronously and clean up
        async for chunk in _iter_file_chunks(path):
            yield chunk

    except Exception as exc:
        # Clean up on error
        try:
            if writer is not None:
                await asyncio.to_thread(writer.close)
        except Exception:
            pass
        try:
            await asyncio.to_thread(os.remove, path)
        except Exception:
            pass

        logger.exception("error streaming parquet", error=str(exc))
        raise HTTPException(
            status_code=500,
            detail=f"Error generating Parquet: {str(exc)}",
        )


class DatasetMetadata(BaseModel):
    name: str
    table_schema: dict
    row_count: int


def create_dataset_router() -> APIRouter:
    router = APIRouter(tags=["Planar Datasets"])

    @router.get("/schemas", response_model=list[str])
    async def get_schemas():
        validate_authorization_for(
            DatasetResource(), DatasetAction.DATASET_LIST_SCHEMAS
        )
        schemas = await list_schemas()
        return schemas

    @router.get("/metadata", response_model=list[DatasetMetadata])
    async def list_planar_datasets(
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        schema_name: str = Query("main"),
    ):
        validate_authorization_for(DatasetResource(), DatasetAction.DATASET_LIST)
        datasets = await list_datasets(limit, offset)

        dataset_names = [dataset.name for dataset in datasets]
        metadata_by_dataset = await get_datasets_metadata(dataset_names, schema_name)

        response = []
        for dataset in datasets:
            metadata = metadata_by_dataset.get(dataset.name)

            if not metadata:
                continue

            schema = metadata["schema"]
            row_count = metadata["row_count"]

            response.append(
                DatasetMetadata(
                    name=dataset.name,
                    row_count=row_count,
                    table_schema={
                        field_name: str(field_type)
                        for field_name, field_type in schema.items()
                    },
                )
            )

        return response

    @router.get("/metadata/{dataset_name}", response_model=DatasetMetadata)
    async def get_planar_dataset(dataset_name: str, schema_name: str = "main"):
        validate_authorization_for(
            DatasetResource(dataset_name=dataset_name),
            DatasetAction.DATASET_VIEW_DETAILS,
        )
        try:
            metadata = await get_dataset_metadata(dataset_name, schema_name)

            if not metadata:
                raise HTTPException(
                    status_code=404, detail=f"Dataset {dataset_name} not found"
                )

            schema = metadata["schema"]
            row_count = metadata["row_count"]

            return DatasetMetadata(
                name=dataset_name,
                row_count=row_count,
                table_schema={
                    field_name: str(field_type)
                    for field_name, field_type in schema.items()
                },
            )
        except (DatasetNotFoundError, TableNotFound):
            raise HTTPException(
                status_code=404, detail=f"Dataset {dataset_name} not found"
            )

    @router.get(
        "/content/{dataset_name}/arrow-stream", response_class=StreamingResponse
    )
    async def stream_dataset_content(
        dataset_name: str,
        batch_size: int = Query(100, ge=1, le=1000),
        limit: int | None = Query(None, ge=1),
    ):
        validate_authorization_for(
            DatasetResource(dataset_name=dataset_name),
            DatasetAction.DATASET_STREAM_CONTENT,
        )
        try:
            dataset = await get_dataset(dataset_name)

            # Apply limit parameter if specified
            table = await dataset.read(limit=limit)

            schema = table.schema().to_pyarrow()

            async def stream_content() -> AsyncGenerator[bytes, None]:
                sink = io.BytesIO()

                try:
                    with pa.ipc.new_stream(sink, schema) as writer:
                        yield sink.getvalue()  # yield the schema

                        batch_count = 0
                        for batch in table.to_pyarrow_batches(chunk_size=batch_size):
                            # reset the sink to only stream
                            # the current batch
                            # we don't want to stream the schema or previous
                            # batches again
                            sink.seek(0)
                            sink.truncate(0)

                            writer.write_batch(batch)
                            yield sink.getvalue()
                            batch_count += 1

                        # For empty datasets, ensure we have a complete stream
                        if batch_count == 0:
                            # Write an empty batch to ensure valid Arrow stream format
                            empty_batch = pa.RecordBatch.from_arrays(
                                [pa.array([], type=field.type) for field in schema],
                                schema=schema,
                            )
                            sink.seek(0)
                            sink.truncate(0)
                            writer.write_batch(empty_batch)
                            yield sink.getvalue()
                finally:
                    # Explicit BytesIO cleanup for memory safety
                    sink.close()

            return StreamingResponse(
                stream_content(),
                media_type="application/vnd.apache.arrow.stream",
                headers={
                    "Content-Disposition": f"attachment; filename={dataset_name}.arrow",
                    "X-Batch-Size": str(batch_size),
                    "X-Row-Limit": str(limit) if limit else "unlimited",
                },
            )
        except (DatasetNotFoundError, TableNotFound):
            raise HTTPException(
                status_code=404, detail=f"Dataset {dataset_name} not found"
            )

    @router.get("/content/{dataset_name}/download")
    async def download_dataset(
        dataset_name: str,
        schema_name: str = "main",
        format: Literal["parquet", "csv"] = Query(
            "parquet", description="Output format for the dataset"
        ),
    ):
        validate_authorization_for(
            DatasetResource(dataset_name=dataset_name),
            DatasetAction.DATASET_DOWNLOAD,
        )

        try:
            dataset = await get_dataset(dataset_name, schema_name)

            if format == "parquet":
                table = await dataset.read()

                return StreamingResponse(
                    stream_parquet(table, batch_size=BATCH_SIZE),
                    media_type="application/x-parquet",
                    headers={
                        "Content-Disposition": f"attachment; filename={dataset_name}.parquet"
                    },
                )

            elif format == "csv":
                table = await dataset.read()

                return StreamingResponse(
                    stream_csv(table, batch_size=BATCH_SIZE),
                    media_type="text/csv",
                    headers={
                        "Content-Disposition": f"attachment; filename={dataset_name}.csv"
                    },
                )

            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported format: {format}",
                )

        except (DatasetNotFoundError, TableNotFound):
            raise HTTPException(
                status_code=404, detail=f"Dataset {dataset_name} not found"
            )

    return router
