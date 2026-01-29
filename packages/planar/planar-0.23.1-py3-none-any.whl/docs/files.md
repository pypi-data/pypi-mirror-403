# Files

## Overview

PlanarFile is the lightweight, serializable reference used by workflows, agents, and
IO tasks to represent uploaded files. The file metadata is stored in the database while
content is stored in the configured backend (local directory, S3-compatible, or Azure
Blob Storage).

## PlanarFile Basics

```python
from planar.files import PlanarFile

async def ingest_file(file: PlanarFile) -> int:
    metadata = await file.get_metadata()
    content = await file.get_content()
    return metadata.size
```

`PlanarFile` stores only metadata in workflow steps. Fetch content via
`PlanarFile.get_content()` when needed.

## Uploading Files

### API

- `POST /planar/v1/file/upload`

Upload one or more files as `multipart/form-data`. The response is a list of
`PlanarFile` metadata objects.

### Programmatic Uploads

```python
from pathlib import Path
from planar.files import PlanarFile

async def upload_report(path: Path) -> PlanarFile:
    return await PlanarFile.upload(content=path, filename=path.name)
```

## Fetching Content and Metadata

- `GET /planar/v1/file/{file_id}/content`
- `GET /planar/v1/file/{file_id}/metadata`

If the storage backend supports external URLs, the content endpoint responds with a
redirect. Otherwise it streams the content directly.

## Storage Configuration

Configure storage in your Planar config:

```yaml
storage:
  backend: localdir
  directory: .data/files
```

Supported backends:

- `localdir`
- `s3`
- `azure_blob`

## Best Practices

- Treat `PlanarFile` as an immutable reference; store the file id in entities when
  you need durable links.
- Avoid loading large files into memory; stream content when possible.
- Use `IO.upload.file(...)` for human-driven uploads inside workflows.
