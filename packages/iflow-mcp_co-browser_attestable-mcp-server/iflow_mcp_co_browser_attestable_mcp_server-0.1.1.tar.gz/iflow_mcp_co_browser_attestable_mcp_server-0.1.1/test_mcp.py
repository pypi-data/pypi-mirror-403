#!/usr/bin/env python3
import asyncio
import json
import sys
import subprocess
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_mcp_server():
    """测试 MCP 服务器"""
    # 启动服务器进程
    env = {
        "PYTHONPATH": "/app/auto-mcp-upload/data/2437/src"
    }
    
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "attestable_mcp_server.server",
        "--skip-ra-tls",
        "--transport",
        "stdio",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={**subprocess.os.environ, **env}
    )
    
    # 等待服务器启动
    await asyncio.sleep(2)
    
    if process.returncode is not None:
        stderr = await process.stderr.read()
        print(f"❌ 服务器启动失败: {stderr.decode()}")
        return False
    
    print("✅ 服务器启动成功")
    
    # 发送初始化请求
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }
    
    process.stdin.write(json.dumps(init_request).encode() + b'\n')
    await process.stdin.drain()
    
    # 读取响应
    response_line = await asyncio.wait_for(process.stdout.readline(), timeout=10)
    response = json.loads(response_line.decode())
    
    if "error" in response:
        print(f"❌ 初始化失败: {response['error']}")
        return False
    
    print("✅ 初始化成功")
    
    # 发送 list_tools 请求
    list_tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    process.stdin.write(json.dumps(list_tools_request).encode() + b'\n')
    await process.stdin.drain()
    
    # 读取响应
    response_line = await asyncio.wait_for(process.stdout.readline(), timeout=10)
    response = json.loads(response_line.decode())
    
    if "error" in response:
        print(f"❌ list_tools 失败: {response['error']}")
        return False
    
    if "result" in response and "tools" in response["result"]:
        tools = response["result"]["tools"]
        print(f"🎉 成功获取到 {len(tools)} 个工具:")
        for i, tool in enumerate(tools, 1):
            print(f"   {i}. {tool.get('name', '未知')}: {tool.get('description', '无描述')}")
        return True
    else:
        print("❌ 响应格式不正确")
        return False
    
    # 清理
    process.terminate()
    await process.wait()

if __name__ == "__main__":
    try:
        success = asyncio.run(test_mcp_server())
        if success:
            print("\n✅ 本地测试通过！")
            sys.exit(0)
        else:
            print("\n❌ 本地测试失败！")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)