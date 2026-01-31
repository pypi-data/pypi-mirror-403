# Developer guide to contribute to Devopness MCP Server

## Local Development

To run from source on tools such as Claude, Cursor, Visual Studio Code, Windsurf, etc

1. Find and edit the `mcp.json` file on your favorite tool
1. Add `devopness` MCP Server as exemplified below

### Using STDIO

Connect using:

#### Cursor (~/.cursor/mcp.json)

```json
{
  "mcpServers": {
    "devopness": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/full/path/to/devopness-ai/mcp-server",
        "devopness-mcp-server",
        "--transport",
        "stdio"
      ],
      "env": {
        "DEVOPNESS_USER_EMAIL": "YOUR_DEVOPNESS_USER_EMAIL",
        "DEVOPNESS_USER_PASSWORD": "YOUR_DEVOPNESS_USER_PASSWORD"
      }
    }
  }
}
```

#### VSCode (~/.config/Code/User/settings.json)

```json
{
  "mcp": {
    "servers": {
      "devopness": {
        "command": "uv",
        "args": [
          "run",
          "--directory",
          "/full/path/to/devopness-ai/mcp-server",
          "devopness-mcp-server",
          "--transport",
          "stdio"
        ],
        "env": {
          "DEVOPNESS_USER_EMAIL": "YOUR_DEVOPNESS_USER_EMAIL",
          "DEVOPNESS_USER_PASSWORD": "YOUR_DEVOPNESS_USER_PASSWORD"
        }
      }
    }
  }
}
```

### Using HTTP server

**Run local HTTP server**:

```shell
cd "/full/path/to/devopness-ai/mcp-server"

# Copy the .env.example file to .env
cp .env.example .env

# Run the mcp server
uv run devopness-mcp-server --host localhost --port 8000
```

Then connect using:

#### Cursor

```json
{
  "mcpServers": {
    "devopness": {
      "url": "http://localhost:8000/mcp/",
    }
  }
}
```

#### VSCode

```json
{
  "mcp": {
    "servers": {
      "devopness": {
        "type": "http",
        "url": "http://localhost:8000/mcp/",
      }
    }
  }
}
```

## Testing and Debugging

### Run with MCP Inspector

```shell
# --- Setup the MCP Server configuration --- #

# Go to the MCP Server directory
cd "/full/path/to/devopness-ai/mcp-server"

# Copy the .env.example file to .env
cp .env.example .env

# --- Using Official MCP Inspector --- #

# In one terminal, run the mcp server
uv run devopness-mcp-server

# In another terminal, run the inspector
npx -y @modelcontextprotocol/inspector

# Configuration must be set in the inspector web interface:
#   Transport Type = Streamble HTTP
#   URL = http://localhost:8000/mcp/

# --- Using alpic.ai MCP Inspector --- #

# In one terminal, run the inspector and the mcp server in stdio
npx -y @alpic-ai/grizzly uv run devopness-mcp-server --transport stdio

# Environment variables must be set in the inspector web interface:
#   DEVOPNESS_USER_EMAIL=<YOUR_DEVOPNESS_USER_EMAIL>
#   DEVOPNESS_USER_PASSWORD=<YOUR_DEVOPNESS_USER_PASSWORD>
```

### Run on Postman

Follow Postman guide to [create an MCP Request](https://learning.postman.com/docs/postman-ai-agent-builder/mcp-requests/create/)

* Choose `STDIO`
* Use the server command:

```shell
uv run --directory "/full/path/to/devopness-ai/mcp-server" devopness-mcp-server --transport stdio
```

## Publishing to the OSS MCP Community Registry

The [OSS MCP Community Registry](https://registry.modelcontextprotocol.io/) lets the community share MCP Servers.
We use the [mcp-publisher CLI](https://github.com/modelcontextprotocol/registry/blob/main/docs/guides/publishing/publish-server.md#step-1-install-the-publisher-cli) to publish the **Devopness MCP Server**.

### Steps

1. **Check server details**

    Make sure the `server.json` file is correct

2. **Install the publisher CLI**

    Download `mcp-publisher` from [here](https://github.com/modelcontextprotocol/registry/blob/main/docs/guides/publishing/publish-server.md#step-1-install-the-publisher-cli)

3. **Get the private key**

    Find the PEM key in [Credentials & Secrets - Engineering](https://docs.google.com/spreadsheets/d/1TRteYFvePn4tL0EcH5zKLodZa7cmOevd9XUKxSLP0BE/edit?pli=1&gid=0#gid=0) under: `MCP > OSS MCP Community Registry > Private Key PEM`

    Save it locally as `key.pem`

4. **Log in to the registry**

    ```bash
    ./mcp-publisher login http \
      --domain mcp.devopness.com \
      --private-key $(openssl pkey -in key.pem -noout -text | grep -A3 "priv:" | tail -n +2 | tr -d ' :\n')
    ```

5. **Publish the server**

    ```bash
    ./mcp-publisher publish
    ```

6. **Verify listing**

    Check the server appears [here](https://registry.modelcontextprotocol.io/v0/servers?search=com.devopness.mcp/server)

### Authentication Setup

To authenticate with the Registry, our domain (`mcp.devopness.com`) must expose either:

* a **DNS TXT record**, or
* a **Well-Known endpoint**

We use a Well-Known endpoint by adding the `location /.well-known/mcp-registry-auth` to `mcp.devopness.com`. Manage it via [Devopness Virtual Host Variable](https://dogfood-app.devopness.com/projects/25/environments/78/virtual-hosts/52/variables/1685).

> **Note:** See the [full guide](https://github.com/modelcontextprotocol/registry/blob/main/docs/guides/publishing/publish-server.md#step-4-authenticate) for more details.
