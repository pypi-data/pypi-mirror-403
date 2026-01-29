<p align="center">
  <img src="https://github.com/mustafametesengul/webquest-mcp/raw/main/docs/images/logo.svg" alt="WebQuest MCP Logo" width="350">
</p>

# WebQuest MCP

WebQuest MCP is a Model Context Protocol (MCP) server that exposes powerful web search and scraping tools to AI agents and MCP-compatible clients.

For available scrapers and browsers, see the [WebQuest documentation](https://mustafametesengul.github.io/webquest/).

## Installation

Installing using pip:

```bash
pip install webquest-mcp
```

Installing using uv:

```bash
uv add webquest-mcp
```

## Usage

### Starting the server

To start the WebQuest MCP server, run:

```bash
webquest-mcp run
```

The server reads its configuration from environment variables (or a `.env` file loaded automatically). Available settings:

- `OPENAI_API_KEY` (required): OpenAI API key for scrapers.
- `HYPERBROWSER_API_KEY` (required): Hyperbrowser API key.
- `WEBQUEST_MCP_AUTH_SECRET` (optional): JWT secret to enable authenticated requests. Leave unset to disable auth.
- `WEBQUEST_MCP_AUTH_AUDIENCE` (optional, default `webquest-mcp`): JWT audience to validate when auth is enabled.
- `WEBQUEST_MCP_TRANSPORT` (optional, default `stdio`): MCP transport. Supported values: `stdio`, `sse`, `streamable-http`.
- `WEBQUEST_MCP_HOST` (optional, default `localhost`): Host to bind when the transport is HTTP-based.
- `WEBQUEST_MCP_PORT` (optional, default `8000`): Port to use when the transport is HTTP-based.

Example `.env`:

```text
OPENAI_API_KEY=your_openai_api_key
HYPERBROWSER_API_KEY=your_hyperbrowser_api_key
WEBQUEST_MCP_AUTH_SECRET=your_jwt_secret_key
WEBQUEST_MCP_AUTH_AUDIENCE=webquest-mcp
WEBQUEST_MCP_TRANSPORT=streamable-http
WEBQUEST_MCP_HOST=localhost
WEBQUEST_MCP_PORT=8000
```

### Token generation

To generate an authentication token for the MCP client, set the required environment variables and run the generator.

The token generator uses the same `WEBQUEST_MCP_*` prefix as the server.

Required settings:

- `WEBQUEST_MCP_AUTH_SECRET`: JWT secret used by the server.
- `WEBQUEST_MCP_AUTH_SUBJECT`: Identifier for the client receiving the token.

Optional settings:

- `WEBQUEST_MCP_AUTH_AUDIENCE` (default `webquest-mcp`)
- `WEBQUEST_MCP_AUTH_EXPIRATION_DAYS` (default `365`)

Example `.env`:

```text
WEBQUEST_MCP_AUTH_SECRET=your-secret-key
WEBQUEST_MCP_AUTH_SUBJECT=client-name
WEBQUEST_MCP_AUTH_AUDIENCE=webquest-mcp
WEBQUEST_MCP_AUTH_EXPIRATION_DAYS=365
```

Run the generator:

```bash
webquest-mcp token
```

### Docker

Run the published image:

```bash
docker run --rm -p 8000:8000 --env-file .env \
  -e WEBQUEST_MCP_HOST=0.0.0.0 \
  mustafametesengul/webquest-mcp run
```

## Disclaimer

This tool is for educational and research purposes only. The developers of WebQuest MCP are not responsible for any misuse of this tool. Scraping websites may violate their Terms of Service. Users are solely responsible for ensuring their activities comply with all applicable laws and website policies.
