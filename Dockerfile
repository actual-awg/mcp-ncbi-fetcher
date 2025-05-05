# Use Python 3.10+ as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install required packages
RUN pip install --no-cache-dir "mcp[cli]" httpx

# Copy our server file
COPY ncbi_server.py /app/

# Expose port for SSE if needed (optional)
EXPOSE 8000

# Use MCP as entrypoint - This allows direct execution 
ENTRYPOINT ["mcp", "run", "ncbi_server.py"]

# Alternatively, we could use Python directly
# CMD ["python", "ncbi_server.py"]