# zeughaus-mcp

MCP Server - Agentic Workbench backed by Nixery.

Execute commands in ephemeral containers with any combination of Nix packages.

## Installation

### uvx (recommended)

```bash
uvx zeughaus-mcp
```

### Docker

```bash
docker run --rm -i \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /path/to/workspace:/workspace \
  -e NIXERY_REGISTRY_URL=nixery.dev \
  -e HOST_WORKSPACE_ROOT=/workspace \
  ghcr.io/gtarkin/zeughaus_mcp:latest
```

## Configuration

Environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NIXERY_REGISTRY_URL` | Yes | - | Nixery registry URL (e.g., `nixery.dev`) |
| `HOST_WORKSPACE_ROOT` | Yes | - | Workspace path to mount into containers |
| `DOCKER_NETWORK_MODE` | No | `host` | Docker network mode |
| `CONTAINER_TIMEOUT_SECONDS` | No | `300` | Container execution timeout |

## MCP Client Configuration

### Claude Desktop (uvx)

```json
{
  "mcpServers": {
    "zeughaus": {
      "command": "uvx",
      "args": ["zeughaus-mcp"],
      "env": {
        "NIXERY_REGISTRY_URL": "nixery.dev",
        "HOST_WORKSPACE_ROOT": "/path/to/workspace"
      }
    }
  }
}
```

### Claude Desktop (Docker)

```json
{
  "mcpServers": {
    "zeughaus": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        "-v", "/path/to/workspace:/workspace",
        "-e", "NIXERY_REGISTRY_URL=nixery.dev",
        "-e", "HOST_WORKSPACE_ROOT=/workspace",
        "ghcr.io/gtarkin/zeughaus_mcp:latest"
      ]
    }
  }
}
```

## License

MIT
