#!/usr/bin/env python3
import subprocess
import json
import sys

proc = subprocess.Popen(
    ["attestable-mcp-server", "--skip-ra-tls", "--transport", "stdio"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

import time
time.sleep(2)

if proc.poll() is not None:
    stderr = proc.stderr.read().decode()
    print(f"❌ 服务器启动失败: {stderr}")
    sys.exit(1)

print("✅ 服务器启动成功")

# 初始化
init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "clientInfo": {"name": "test", "version": "1.0"}}}
proc.stdin.write(json.dumps(init_req).encode() + b'\n')
proc.stdin.flush()

resp_line = proc.stdout.readline()
resp = json.loads(resp_line.decode())
print(f"初始化响应: {resp}")

if "error" in resp:
    print(f"❌ 初始化失败: {resp['error']}")
    sys.exit(1)

print("✅ 初始化成功")

# list_tools
list_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
proc.stdin.write(json.dumps(list_req).encode() + b'\n')
proc.stdin.flush()

resp_line = proc.stdout.readline()
resp = json.loads(resp_line.decode())
print(f"list_tools响应: {resp}")

if "error" in resp:
    print(f"❌ list_tools失败: {resp['error']}")
    sys.exit(1)

if "result" in resp and "tools" in resp["result"]:
    tools = resp["result"]["tools"]
    print(f"\n🎉 成功获取到 {len(tools)} 个工具:")
    for tool in tools:
        print(f"   - {tool['name']}: {tool['description']}")
else:
    print("❌ 响应格式不正确")
    sys.exit(1)

proc.terminate()
proc.wait()

print("\n✅ 本地测试通过！")