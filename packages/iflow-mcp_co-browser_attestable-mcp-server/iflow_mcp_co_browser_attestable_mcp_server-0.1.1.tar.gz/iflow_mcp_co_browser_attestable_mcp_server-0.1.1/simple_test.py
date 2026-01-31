#!/usr/bin/env python3
import subprocess
import json
import sys
import os

# 设置环境变量
os.environ["PYTHONPATH"] = "/app/auto-mcp-upload/data/2437/src"

# 启动服务器
proc = subprocess.Popen(
    [sys.executable, "-m", "attestable_mcp_server.server", "--skip-ra-tls", "--transport", "stdio"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    env=os.environ
)

# 等待启动
import time
time.sleep(2)

# 初始化
init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "clientInfo": {"name": "test", "version": "1.0"}}}
proc.stdin.write(json.dumps(init_req).encode() + b'\n')
proc.stdin.flush()

resp_line = proc.stdout.readline()
print(f"初始化响应: {resp_line.decode()}")

# list_tools
list_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
proc.stdin.write(json.dumps(list_req).encode() + b'\n')
proc.stdin.flush()

resp_line = proc.stdout.readline()
print(f"list_tools响应: {resp_line.decode()}")

resp = json.loads(resp_line)
if "result" in resp and "tools" in resp["result"]:
    tools = resp["result"]["tools"]
    print(f"✅ 成功获取到 {len(tools)} 个工具")
    for tool in tools:
        print(f"   - {tool['name']}: {tool['description']}")
else:
    print("❌ 测试失败")
    sys.exit(1)

proc.terminate()
proc.wait()