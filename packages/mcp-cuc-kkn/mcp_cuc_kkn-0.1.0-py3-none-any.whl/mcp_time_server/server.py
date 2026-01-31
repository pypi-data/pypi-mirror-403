#!/usr/bin/env python3
"""
MCP Server - Time Service
一个提供时间查询功能的 MCP 服务器
"""

from mcp.server.fastmcp import FastMCP
from datetime import datetime
import pytz
from typing import Optional


mcp = FastMCP("time-server")


@mcp.tool()
def get_current_time(timezone: Optional[str] = None) -> str:
    """
    获取当前时间
    
    Args:
        timezone: 可选参数，指定时区（如 "Asia/Shanghai", "UTC", "America/New_York"）
                  如果不提供，则使用本地系统时区
    
    Returns:
        str: 格式化的当前时间字符串
    
    Examples:
        >>> get_current_time()
        '2026-01-29 14:30:45'
        
        >>> get_current_time("UTC")
        '2026-01-29 06:30:45 UTC'
        
        >>> get_current_time("Asia/Shanghai")
        '2026-01-29 14:30:45 CST'
    """
    if timezone:
        try:
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)
            return now.strftime(f"%Y-%m-%d %H:%M:%S {now.tzinfo.tzname(now)}")
        except pytz.exceptions.UnknownTimeZoneError:
            return f"错误: 未知的时区 '{timezone}'，请使用有效的时区名称（如 'UTC', 'Asia/Shanghai'）"
    else:
        now = datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S")


def main():
    """Main entry point for the MCP Time Server"""
    mcp.run(transport="sse")


if __name__ == "__main__":
    main()
