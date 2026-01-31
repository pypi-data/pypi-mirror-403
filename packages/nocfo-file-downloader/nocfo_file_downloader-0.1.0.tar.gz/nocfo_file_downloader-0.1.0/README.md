# NoCFO File Downloader

CLI tool to download all attachments from a NoCFO business and organize them by document number.

## Features

- Fetches all documents and maps `document_number -> attachment_ids`.
- Downloads every attachment.
- Files linked to a document are saved as:

  `<document_number>/<document_number> <original_filename>`

- Files not linked to any document are saved under:

  `UNCATEGORIZED/<original_filename>`

- Shows a progress bar while downloading.

## Installation

```bash
pip install nocfo-file-downloader
```

## Usage

```bash
nocfo-dl <business_slug> --output-dir ./downloads
```

### Options

- `--output-dir/-o` Output folder (default: `./downloads`)
- `--base-url` API base URL (default: `https://api-prd.nocfo.io`)
- `--page-size` Page size for pagination (default: `200`)
- `--token` PAT token (if omitted, the tool will prompt)
- `--concurrency/-c` Number of concurrent downloads (default: `4`)

## PAT token (Personal Access Token)

The API uses token-based authentication. The token must be passed in the `Authorization` header as:

```
Authorization: Token <your_token_here>
```

You can create and manage tokens in the NoCFO web app under **Account Settings**:

- Production: https://login.nocfo.io/auth/tokens/
- Testing: https://login-tst.nocfo.io/auth/tokens/

The CLI prompts for a token at startup if you do not provide `--token`.

## Examples

Download attachments for business `acme-corp` to `./exports`:

```bash
nocfo-dl acme-corp --output-dir ./exports
```

Use a custom API base URL:

```bash
nocfo-dl acme-corp --base-url https://api-prd.nocfo.io
```

Limit concurrency:

```bash
nocfo-dl acme-corp --concurrency 8
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Run locally:

```bash
python -m nocfo_file_downloader <business_slug>
```

## License

MIT
