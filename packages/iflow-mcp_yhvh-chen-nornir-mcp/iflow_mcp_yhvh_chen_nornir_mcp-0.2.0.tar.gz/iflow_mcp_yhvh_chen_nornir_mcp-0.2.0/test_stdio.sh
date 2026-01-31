#!/bin/bash
# 测试MCP服务器的stdio连接
cd /app/auto-mcp-upload/data/2414

# 发送完整的测试序列
{
  echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
  sleep 0.1
  echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'
  sleep 0.1
  echo '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
  sleep 0.5
} | /app/auto-mcp-upload/.venv/bin/python run_stdio.py 2>/dev/null | grep -A 100 '"result"' | head -50