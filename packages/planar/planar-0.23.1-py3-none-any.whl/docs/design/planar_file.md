# PlanarFile - Unified File Handling Documentation

## Overview

PlanarFile provides unified file handling within the Planar framework. The system consists of:

- `PlanarFile`: A lightweight Pydantic model for file references
- `PlanarFileMetadata`: Database model storing file metadata and storage references  
- Storage abstraction supporting local directory and S3 backends
- API endpoints for file upload, retrieval, and metadata access

The system is designed to be storage-agnostic and supports efficient workflow serialization by passing only lightweight file references rather than file content.

The CoPlane UI handles PlanarFiles natively, displaying them in step and workflow data views and providing upload interfaces for workflow inputs.

## Core Components

### PlanarFile Model

A lightweight Pydantic model for file references within workflows and API responses:

```python
class PlanarFile(BaseModel):
    id: UUID
    filename: str
    content_type: str
    size: int

    async def get_metadata(self) -> "PlanarFileMetadata":
        """Retrieves the full metadata record from the database."""

    async def get_content(self) -> bytes:
        """Retrieves the file content as bytes from storage."""

    @staticmethod
    async def upload(
        content: Union[bytes, AsyncGenerator[bytes, None], Path, str],
        filename: str,
        content_type: str | None = None,
        size: int | None = None,
    ) -> "PlanarFile":
        """Uploads file content to storage and creates metadata record."""
```

### PlanarFileMetadata Database Model

Stores the authoritative mapping between file IDs and storage details:

```python
class PlanarFileMetadata(PlanarFile, TimestampMixin, PlanarInternalBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    storage_ref: str = Field(index=True)  # Backend-specific storage identifier
    # Inherits: filename, content_type, size from PlanarFile
    # Inherits: created_at, updated_at from TimestampMixin
```

The `storage_ref` field contains a backend-specific identifier (UUID for local directory, object key for S3). The storage backend type is determined by application configuration.

### Storage Abstraction

The storage layer provides a common interface for different storage backends:

#### Storage Interface
```python
class Storage(ABC):
    async def put(self, stream: AsyncGenerator[bytes, None], mime_type: str | None = None) -> str
    async def get(self, ref: str) -> tuple[AsyncGenerator[bytes, None], str | None]
    async def delete(self, ref: str) -> None
    async def external_url(self, ref: str) -> str | None
    async def put_bytes(self, data: bytes, mime_type: str | None = None) -> str
    async def get_bytes(self, ref: str) -> tuple[bytes, str | None]
    async def put_string(self, data: str, encoding: str = "utf-8", mime_type: str | None = None) -> str
    async def get_string(self, ref: str, encoding: str = "utf-8") -> tuple[str, str | None]
```

#### Available Backends
- **LocalDirectoryStorage**: Stores files in local filesystem directories
- **S3Storage**: Stores files in S3-compatible object storage
- **AzureBlobStorage**: Stores files in Azure Blob Storage

#### Configuration
```python
# Local directory storage
StorageConfig = LocalDirectoryConfig(backend="localdir", directory="/path/to/storage")

# S3 storage  
StorageConfig = S3Config(
    backend="s3",
    bucket_name="my-bucket",
    region="us-east-1",
    access_key="...",  # Optional
    secret_key="...",  # Optional  
    endpoint_url="..."  # Optional for S3-compatible services
)

# Azure Blob Storage
# Option 1: Connection string (simplest for development)
StorageConfig = AzureBlobConfig(
    backend="azure_blob",
    container_name="my-container",
    connection_string="DefaultEndpointsProtocol=https;AccountName=...",
    sas_ttl=3600,  # Optional: SAS URL expiry in seconds (default: 3600)
)

# Option 2: Azure AD authentication (recommended for production)
StorageConfig = AzureBlobConfig(
    backend="azure_blob",
    container_name="my-container",
    account_url="https://myaccount.blob.core.windows.net",
    use_azure_ad=True,
    sas_ttl=3600,  # Optional: SAS URL expiry in seconds
)

# Option 3: Account key authentication
StorageConfig = AzureBlobConfig(
    backend="azure_blob",
    container_name="my-container",
    account_url="https://myaccount.blob.core.windows.net",
    account_key="...",
    sas_ttl=3600,  # Optional: SAS URL expiry in seconds
)
```

#### Azure Blob Storage Installation
Azure Blob Storage support requires additional dependencies:
```bash
pip install planar[azure]
# or with uv:
uv sync --extra azure
```

#### CORS Configuration
When using Azure Blob Storage with web applications, you need to configure Cross-Origin Resource Sharing (CORS) to allow your frontend applications to access the blob storage directly. This is required when using SAS URLs for direct file uploads or downloads from the browser.

Configure CORS using the Azure CLI:
```bash
# Enable CORS for Blob service
az storage cors add \
  --services b \
  --account-name <ACCOUNT_NAME> \
  --origins "*" \
  --methods GET PUT POST DELETE HEAD OPTIONS \
  --allowed-headers "*" \
  --exposed-headers "*" \
  --max-age 86400
```

Replace `<ACCOUNT_NAME>` with your storage account name.

**Important Notes:**
- CORS is only required if you're using CoPlane's UI to upload and view files.
- You can also configure CORS through the Azure Portal under Storage Account → Settings → CORS

#### Azure Authentication Methods
Azure Blob Storage supports three authentication methods:

1. **Connection String** (recommended for development):
   - Contains all necessary connection information in a single string
   - Simplest to configure for local development and testing
   - Supports SAS URL generation for `external_url()`

2. **Azure AD Authentication** (recommended for production):
   - Uses `DefaultAzureCredential` for authentication
   - Works seamlessly with Azure Managed Identity, Service Principals, and Azure CLI
   - Best security practice for applications deployed in Azure
   - Supports User Delegation SAS URL generation for `external_url()`

3. **Account Key Authentication** (traditional approach):
   - Uses explicit account name and key
   - Supports SAS URL generation for `external_url()`
   - Requires managing storage account keys

#### Example Azure Configurations
```yaml
# Option 1: Azure AD authentication (recommended for production)
storage:
  backend: azure_blob
  container_name: planar-files
  account_url: "https://mystorageaccount.blob.core.windows.net"
  use_azure_ad: true
  sas_ttl: 3600  # Optional: SAS URL expiry in seconds (default: 3600)

# Option 2: Connection string (simplest for development)  
storage:
  backend: azure_blob
  container_name: planar-files
  connection_string: ${AZURE_STORAGE_CONNECTION_STRING}
  # Note: When using connection_string, do not provide account_url, use_azure_ad, or account_key

# Option 3: Account key authentication
storage:
  backend: azure_blob
  container_name: planar-files
  account_url: "https://mystorageaccount.blob.core.windows.net"
  account_key: ${AZURE_STORAGE_KEY}

# Azurite emulator (local testing with account key)
storage:
  backend: azure_blob
  container_name: planar-files
  account_url: "http://127.0.0.1:10000/devstoreaccount1"
  account_key: "Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw=="
  
# Azurite emulator (local testing with connection string)
storage:
  backend: azure_blob
  container_name: planar-files
  connection_string: "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1"
```

## API Endpoints

The file system provides three main API endpoints:

### Upload Files
`POST /planar/v1/files/upload`
- Accepts `multipart/form-data` with one or more files
- Stores files using the configured storage backend
- Creates `PlanarFileMetadata` records
- Returns `list[PlanarFile]` with file metadata

### Get File Content  
`GET /planar/v1/files/{file_id}/content`
- Retrieves file content by ID
- Returns `RedirectResponse` if storage provides external URL
- Otherwise streams content directly with appropriate MIME type
- Handles missing files with 404 responses

### Get File Metadata
`GET /planar/v1/files/{file_id}/metadata`  
- Returns `PlanarFile` metadata for the specified file ID
- Includes filename, content type, size, and ID information

## Serialization

`PlanarFile` instances serialize to standard JSON using Pydantic's `model_dump()`. This allows them to be:
- Stored in workflow step JSON columns
- Returned by API responses  
- Passed between workflow steps

**Important**: Only file metadata is serialized, not file content. Content must be retrieved separately via `get_content()` or API endpoints.

## Usage Examples

### Creating Files Programmatically

```python
from pathlib import Path
from planar.files.models import PlanarFile

# Upload from bytes
async def create_report_file(report_data: bytes, filename: str):
    planar_file = await PlanarFile.upload(
        content=report_data,
        filename=filename,
        content_type="application/pdf"
    )
    return planar_file

# Upload from file path  
async def create_file_from_path(source_path: Path, filename: str):
    planar_file = await PlanarFile.upload(
        content=source_path,
        filename=filename
        # content_type and size inferred automatically
    )
    return planar_file

# Upload from async generator
async def create_from_stream(stream: AsyncGenerator[bytes, None], filename: str):
    planar_file = await PlanarFile.upload(
        content=stream,
        filename=filename,
        content_type="application/octet-stream",
        size=1024  # Must specify size for streams
    )
    return planar_file
```

### Reading File Content

```python
async def process_file(planar_file: PlanarFile):
    # Get file content as bytes
    content = await planar_file.get_content()
    
    # Get full metadata record
    metadata = await planar_file.get_metadata()
    
    # Access file properties
    print(f"File: {planar_file.filename}")
    print(f"Size: {planar_file.size} bytes")
    print(f"Type: {planar_file.content_type}")
```

### API Client Usage

```python
import httpx

# Upload files via API
async def upload_files(files: list[Path]):
    async with httpx.AsyncClient() as client:
        form_data = []
        for file_path in files:
            form_data.append(("files", (file_path.name, file_path.open("rb"))))
        
        response = await client.post("/planar/v1/files/upload", files=form_data)
        planar_files = [PlanarFile(**item) for item in response.json()]
        return planar_files

# Download file content
async def download_file(file_id: str, output_path: Path):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"/planar/v1/files/{file_id}/content")
        
        if response.status_code == 302:  # Redirect to external URL
            download_url = response.headers["location"]
            response = await client.get(download_url)
        
        output_path.write_bytes(response.content)
```

## Implementation Status

### Completed Features
- ✅ Core models: `PlanarFile` and `PlanarFileMetadata`
- ✅ Storage abstraction with `Storage` interface
- ✅ Local directory, S3, and Azure Blob Storage backends
- ✅ API endpoints for upload, content retrieval, and metadata
- ✅ `PlanarFile.upload()` utility method
- ✅ Basic test coverage for storage and models
- ✅ Storage configuration and context management
- ✅ Azure AD authentication support for production deployments

### Future Enhancements
- **Framework Integration**: Model field integration (`AttachmentField`), agent/human step integration
- **Storage Features**: Garbage collection, pre-signed URLs, additional backends (Google Cloud Storage, Backblaze, etc.)
- **Access Control**: Permissions and security for file access
- **Performance**: File content caching, enhanced streaming for large files
- **Versioning**: Support for file versioning and history

## Getting Started

1. **Configure Storage**: Set up storage backend in your application configuration
2. **Import Models**: Use `from planar.files import PlanarFile, PlanarFileMetadata`
3. **Upload Files**: Use `PlanarFile.upload()` or API endpoints
4. **Reference Files**: Include `PlanarFile` objects in your Pydantic models
5. **Access Content**: Use `get_content()` method or API endpoints when needed
