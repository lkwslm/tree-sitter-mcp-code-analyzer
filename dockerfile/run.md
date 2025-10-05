docker run -d \
  --name mcp-analyzer \
  -p 8000:8000 \
  -v $(pwd):/app \
  -v $(pwd)/workspace/repo:/workspace/repo \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/cache:/app/cache \
  -v $(pwd)/logs:/app/logs \
  tree-sitter-mcp-analyzer


