#!/usr/bin/env python3
"""
手动测试MCP服务器
"""
import asyncio
import sys
import os

# 确保cmcp模块可以被找到
sys.path.insert(0, '/app/auto-mcp-upload/data/2392')

async def test_mcp():
    """测试MCP服务器"""
    # 设置环境变量
    os.environ['TOOLS_ENABLE_KB'] = 'false'
    os.environ['TOOLS_ENABLE_SYSTEM'] = 'false'
    
    # 导入MCP服务器
    from mcp.client.stdio import stdio_client
    from mcp import ClientSession
    
    # 启动服务器进程
    import subprocess
    process = subprocess.Popen(
        ['/app/venv/bin/python3', '-m', 'cmcp.main', '--test-mode'],
        cwd='/app/auto-mcp-upload/data/2392',
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # 等待一下让服务器启动
    await asyncio.sleep(2)
    
    # 检查进程是否还在运行
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        print(f"服务器启动失败:")
        print(f"stdout: {stdout}")
        print(f"stderr: {stderr}")
        return False
    
    print("✓ MCP服务器启动成功")
    
    # 尝试连接
    try:
        async with stdio_client(process.stdin, process.stdout) as (read, write):
            async with ClientSession(read, write) as session:
                # 初始化连接
                await session.initialize()
                print("✓ MCP连接初始化成功")
                
                # 列出工具
                result = await session.list_tools()
                print(f"✓ 发现 {len(result.tools)} 个工具:")
                for tool in result.tools:
                    print(f"  - {tool.name}: {tool.description[:50]}...")
                
                print(f"\n✓ 本地测试通过！共发现 {len(result.tools)} 个工具")
                return True
    except Exception as e:
        print(f"✓ MCP连接失败: {e}")
        return False
    finally:
        # 清理进程
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

if __name__ == "__main__":
    success = asyncio.run(test_mcp())
    sys.exit(0 if success else 1)