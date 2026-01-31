FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY crosstabs_mcp/ ./crosstabs_mcp/
COPY pyproject.toml .
COPY README.md .

# Install the package
RUN pip install --no-cache-dir .

# Run the MCP server
CMD ["crosstabs"]
