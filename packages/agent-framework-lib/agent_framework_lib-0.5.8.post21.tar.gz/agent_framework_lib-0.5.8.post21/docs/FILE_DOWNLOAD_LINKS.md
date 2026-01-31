# File Download Links

## Overview

When an agent creates a file using the file storage system, the response includes a download URL that allows users to download the file directly from the UI.

## How It Works

### Backend Flow

1. **Tool creates file**: When an agent tool (e.g., `CreateFileTool`, `CreatePDFFromMarkdownTool`) stores a file, it returns a message containing the download URL:
   ```
   File 'test.txt' created successfully!
   
   Download link: [test.txt](/files/{file_id}/download)
   ```

2. **Server processes response**: The server's `process_response_file_links()` function scans the response text for any markdown links containing UUIDs and normalizes them to the standard format `/files/{file_id}/download`.

3. **Download endpoint**: The `/files/{file_id}/download` endpoint retrieves the file from storage and returns it with appropriate headers for download.

### Frontend Flow

1. **Markdown rendering**: The `modern_ui.html` frontend renders markdown content using `marked.js`.

2. **URL detection**: The `convertFileUrlsToLinks()` function scans rendered content for file download URLs matching the pattern `/files/{uuid}/download`.

3. **Button creation**: Detected URLs are converted to styled download buttons with:
   - Blue gradient background
   - Download icon (📥)
   - Click handler that triggers the download

## URL Format

The standard download URL format is:
```
/files/{file_id}/download
```

Where `{file_id}` is a UUID (e.g., `e5c6532b-a6d3-4c03-947c-41de0a6a5c91`).

## Tools That Generate Download Links

| Tool | Description |
|------|-------------|
| `CreateFileTool` | Creates text files |
| `CreatePDFFromMarkdownTool` | Creates PDFs from markdown |
| `CreatePDFFromHTMLTool` | Creates PDFs from HTML |
| `CreatePDFWithImagesTool` | Creates PDFs with embedded images |
| `ChartToImageTool` | Creates chart images |
| `MermaidToImageTool` | Creates Mermaid diagram images |
| `TableToImageTool` | Creates table images |

## API Endpoints

### Download File
```
GET /files/{file_id}/download
```

Returns the file content with appropriate `Content-Disposition` header for download.

### Get File Metadata
```
GET /files/{file_id}
```

Returns file metadata (filename, mime_type, size, etc.).

### Preview File
```
GET /files/{file_id}/preview
```

Returns file preview data for supported file types.

## Troubleshooting

### Links not clickable
- Ensure the frontend has been refreshed (Cmd+Shift+R / Ctrl+Shift+R)
- Check browser console for JavaScript errors
- Verify the URL format matches `/files/{uuid}/download`

### File not found errors
- Verify the file was stored successfully (check server logs)
- Ensure the file storage backend is properly configured
- Check that `LOCAL_STORAGE_PATH` environment variable is set

### Download fails
- Check server logs for storage errors
- Verify file permissions on the storage directory
- Ensure the file hasn't been deleted
