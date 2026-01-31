# Parze Python SDK

Official Python client for the Parze document parsing API.

## Installation
```bash
pip install parze
```

## Quick Start

```python
from parze import ParzeClient

# Initialize client with your API key
client = ParzeClient(api_key="pk_live_your_key_here")

# Parse a document
result = client.parse("invoice.pdf")
print(result["text"])

# Extract structured data (one step)
schema = {
    "invoice_number": {"type": "string", "description": "Invoice number"},
    "total_amount": {"type": "string", "description": "Total amount"},
    "date": {"type": "string", "description": "Invoice date"}
}
extraction = client.extract(file="invoice.pdf", extraction_schema=schema)
print(extraction["extraction"])

# To avoid double billing, parse first and then extract with job_id
parse_result = client.parse("invoice.pdf")
extraction = client.extract(parse_result["text"], schema, parse_result["job_id"])

# Get AI-suggested schema
suggested = client.suggest_schema(text)
print(suggested)
```

## API Reference

### `parse(file, output_format="structured", preserve_tables=True, preserve_layout=True, extraction_mode="auto")`
Parse a document into structured text.

**Parameters:**
- `file` (str or file object): Path to file or file object
- `output_format` (str): "structured", "markdown", or "json"
- `preserve_tables` (bool): Preserve table structure
- `preserve_layout` (bool): Preserve document layout
- `extraction_mode` (str): "auto", "ocr_only", "llm_only", or "identity_doc"

**Returns:** Dict with parsed text and metadata

### `extract(text=None, extraction_schema=None, job_id=None, file=None)`
Extract structured data from a file or parsed text using a schema.

**Parameters:**
- `text` (str, optional): Document text (from parse)
- `extraction_schema` (dict, required): Schema defining fields to extract
- `job_id` (str, required if text is provided): Job ID from parse response
- `file` (str or file object, optional): Path to file or file object (if provided, parse runs internally)

**Returns:** Dict with extracted data and confidence scores

### `suggest_schema(text)`
Get AI-suggested extraction schema based on document text.

**Parameters:**
- `text` (str): Document text

**Returns:** Dict with suggested schema

### `text_to_schema(description)`
Convert natural language description to extraction schema.

**Parameters:**
- `description` (str): Natural language description of fields

**Returns:** Dict with generated schema

## Get API Key

Get your API key from [platform.parze.ai](https://platform.parze.ai)
