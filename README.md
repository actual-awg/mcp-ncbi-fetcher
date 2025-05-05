to get this running you will need to clone the repository and cd into the directory, then run:

# Build the container
docker build -t ncbi-mcp-server .

# Run with stdio transport (for Claude Desktop)
docker run -it --rm ncbi-mcp-server

make sure you add this to claude_desktop_config.json ($env:AppData\Claude\claude_desktop_config.json on windows)
json{
  "mcpServers": {
    "ncbi-sequence-fetcher": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "ncbi-mcp-server"
      ]
    }
  }
}
