---
title: MarkItDown MCP
tags: [mcp, markitdown, document-conversion, microsoft]
status: active
source: https://github.com/microsoft/markitdown/tree/main/packages/markitdown-mcp
---

# MarkItDown MCP Server

> Convert any file or URL to clean Markdown — PDFs, Word docs, PowerPoint, HTML, images, audio, and more.

## What It Does

[MarkItDown](https://github.com/microsoft/markitdown) is a Microsoft tool that converts almost any document format to Markdown. The MCP server exposes this as a single tool your AI can call.

### Supported Input Formats

| Format | Notes |
|--------|-------|
| PDF | Text extraction |
| Word (`.docx`) | Full formatting |
| PowerPoint (`.pptx`) | Slides as Markdown |
| Excel (`.xlsx`) | Tables as Markdown |
| HTML / Web URLs | Cleans navigation, ads |
| Images | OCR + EXIF metadata |
| Audio (`.mp3`, `.wav`) | Speech-to-text transcription |
| ZIP archives | Converts contents |
| Jupyter notebooks (`.ipynb`) | Code + output |

## Available Tools

| Tool | Description |
|------|-------------|
| `convert_to_markdown(uri)` | Convert any `http:`, `https:`, `file:`, or `data:` URI to Markdown |

## Docker Compose Config

```yaml
markitdown-mcp:
  image: python:3.12-slim
  command: >
    sh -c "pip install markitdown-mcp &&
           markitdown-mcp --http --host 0.0.0.0 --port 3001"
  volumes:
    - ./data/markitdown:/workdir:ro
  ports:
    - "8005:3001"
```

Files placed in `./data/markitdown/` on your host are accessible inside the container at `/workdir/`.

## MCP Client Configuration

```json
{
  "mcpServers": {
    "markitdown": {
      "url": "http://localhost:8005/mcp",
      "transport": "http"
    }
  }
}
```

## Usage Examples

### Convert a web page

```
"Convert https://docs.python.org/3/library/asyncio.html to Markdown"
```

### Convert a local file

1. Copy the file to `./data/markitdown/report.pdf`
2. Ask AI: `"Convert /workdir/report.pdf to Markdown and summarize it"`

### Convert from a URL (via the API directly)

```bash
curl -X POST http://localhost:8005/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "convert_to_markdown",
      "arguments": {"uri": "https://example.com"}
    }
  }'
```

## Security Considerations

> ⚠️ **Important**: MarkItDown MCP runs with the privileges of the Docker process. It can read any file mounted into the container.

Best practices:
- Only mount directories you intend to expose (`./data/markitdown:/workdir:ro`)
- The `:ro` (read-only) flag in the volume mount prevents writes
- Do not bind to `0.0.0.0` in a network-facing environment unless behind a firewall
- Do not mount sensitive directories (SSH keys, credentials, etc.)

## Troubleshooting

- **"File not found"** — Make sure the file is in `./data/markitdown/` and use the path `/workdir/filename` in the URI
- **PDF extraction is empty** — The PDF may be image-based; MarkItDown will attempt OCR but results vary
- **Slow audio transcription** — Audio files use Whisper; the first run downloads the model (~150MB)
- **Port 8005 conflict** — Change the host port in `docker-compose.yml` (`"8006:3001"`)

## References

- [[MCP Stack]] — Back to main stack overview
- Source: https://github.com/microsoft/markitdown
- PyPI: https://pypi.org/project/markitdown-mcp/
