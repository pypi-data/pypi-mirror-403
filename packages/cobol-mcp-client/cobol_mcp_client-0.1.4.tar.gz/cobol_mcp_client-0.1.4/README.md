# cobol-mcp-client

An MCP (Model Context Protocol) server for COBOL development assistance. Provides static analysis with blind-spot detection and hybrid documentation search.

## Quick Start

### Automatic Setup (Recommended) ✨

```bash
pipx run cobol-mcp-client setup YOUR_API_KEY
```

This automatically configures Cursor. For other IDEs:

```bash
pipx run cobol-mcp-client setup YOUR_API_KEY --ide claude-desktop
pipx run cobol-mcp-client setup YOUR_API_KEY --ide vscode
pipx run cobol-mcp-client setup YOUR_API_KEY --ide windsurf
pipx run cobol-mcp-client setup YOUR_API_KEY --ide amp
```

List all supported IDEs:

```bash
pipx run cobol-mcp-client list-ides
```

### Manual Setup

If you prefer manual configuration, add to your IDE's MCP config:

```json
{
  "mcpServers": {
    "cobol": {
      "command": "uvx",
      "args": ["cobol-mcp-client"],
      "env": {
        "COBOL_MCP_API_KEY": "your-api-key"
      }
    }
  }
}
```

Config file locations:
- **Cursor**: `~/.cursor/mcp.json`
- **Claude Desktop**: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
- **VS Code**: `~/.vscode/mcp.json`
- **Windsurf**: `~/.codeium/windsurf/mcp_config.json`

## What It Does

Three capabilities exposed as MCP tools/resources:

1. **`check`** - Static analysis of COBOL source code. Runs 30+ rules covering general COBOL issues (unused variables, missing FILE STATUS, arithmetic without ON SIZE ERROR) and IMS-specific patterns (missing status checks, GB handling, SSA correctness, checkpoint discipline).

2. **`search`** - Hybrid semantic + keyword search across COBOL documentation. Queries a backend API that performs dense vector search, sparse BM25 search, and reranking.

3. **`translate_reference`** - COBOL-to-Java translation patterns and guidance.

4. **Resources** - `cobol://context`, `cobol://rules`, `cobol://gnucobol` for reference documentation.

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `COBOL_MCP_API_KEY` | Yes | API key for documentation search |
| `COBOL_MCP_API_URL` | No | Backend API URL (defaults to production) |

## Architecture

```
cobol_mcp/
├── server.py          # FastMCP server entry point
├── cli.py             # CLI for setup command
├── setup.py           # IDE configuration utilities
├── tools/
│   ├── check.py       # Invokes rules engine on source text
│   ├── search.py      # HTTP proxy to backend search API
│   └── translate.py   # Translation reference lookup
├── rules/
│   ├── parser.py      # COBOL structure extractor
│   ├── general.py     # General COBOL rules (COB-001 through COB-005)
│   ├── ims.py         # IMS-specific rules (IMS-001 through IMS-170)
│   ├── lookup.py      # Rule documentation lookup
│   └── models.py      # Finding dataclass
└── resources/
    ├── context.md     # Dialect context guide
    ├── rules.md       # Full rule documentation
    ├── gnucobol.md    # GnuCOBOL compiler reference
    └── translate/     # Translation reference files
```

## Development

```bash
pip install -e .
python -m pytest tests/ -v   # 412 tests
```

## License

Proprietary.
