FROM python:3.11-slim

WORKDIR /app

# Install package
COPY . .
RUN pip install --no-cache-dir .

# Environment variables (override at runtime)
ENV JIS_IDENTITY=""
ENV JIS_SECRET=""
ENV HUMOTICA_JIS_ENDPOINT="https://humotica.com/.well-known/jis"

# Run the MCP server
ENTRYPOINT ["mcp-server-did-jis"]
