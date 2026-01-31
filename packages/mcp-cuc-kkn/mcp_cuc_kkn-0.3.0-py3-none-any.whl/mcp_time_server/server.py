#!/usr/bin/env python3
"""
MCP Server - Time Service
一个提供时间查询功能的 MCP 服务器
"""

from mcp.server import Server
from mcp.types import Tool, TextContent
from datetime import datetime
import pytz
from typing import Optional
import asyncio


async def get_current_time_handler(args: dict) -> list[TextContent]:
    """
    处理获取当前时间的请求
    
    Args:
        args: 包含 timezone 参数的字典
    
    Returns:
        list[TextContent]: 包含时间信息的文本内容
    """
    timezone = args.get("timezone")
    
    if timezone:
        try:
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)
            time_str = now.strftime(f"%Y-%m-%d %H:%M:%S {now.tzinfo.tzname(now)}")
            return [TextContent(type="text", text=time_str)]
        except pytz.exceptions.UnknownTimeZoneError:
            error_msg = f"错误: 未知的时区 '{timezone}'，请使用有效的时区名称（如 'UTC', 'Asia/Shanghai'）"
            return [TextContent(type="text", text=error_msg)]
    else:
        now = datetime.now()
        time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        return [TextContent(type="text", text=time_str)]


async def main():
    """主函数：启动 MCP 服务器"""
    
    server = Server("time-server", "0.2.0")
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """列出可用的工具"""
        return [
            Tool(
                name="get_current_time",
                description="获取当前时间，支持可选的时区参数",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "可选参数，指定时区（如 'Asia/Shanghai', 'UTC', 'America/New_York'）"
                        }
                    }
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, args: dict) -> list[TextContent]:
        """调用工具"""
        if name == "get_current_time":
            return await get_current_time_handler(args)
        else:
            return [TextContent(type="text", text=f"未知工具: {name}")]
    
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
