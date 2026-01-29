#!/usr/bin/env python3
"""MCP Timer Server - Provides wait and scheduled timing functionality"""

import asyncio
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("timer")

@mcp.tool()
async def wait(seconds: int) -> str:
    """Wait for specified seconds"""
    await asyncio.sleep(seconds)
    return f"Waited {seconds} seconds, current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

@mcp.tool()
async def wait_until(target_time: str, next_day_if_passed: bool = False) -> str:
    """Wait until specified time (format: HH:MM:SS or YYYY-MM-DD HH:MM:SS)
    
    Args:
        target_time: Target time
        next_day_if_passed: If time has passed, wait until same time tomorrow (only for HH:MM:SS format)
    """
    now = datetime.now()
    try:
        if len(target_time) <= 8:
            target = datetime.strptime(target_time, "%H:%M:%S").replace(
                year=now.year, month=now.month, day=now.day
            )
            if target <= now:
                if next_day_if_passed:
                    target = target + timedelta(days=1)
                else:
                    return f"Target time {target_time} has passed, current time: {now.strftime('%H:%M:%S')}"
        else:
            target = datetime.strptime(target_time, "%Y-%m-%d %H:%M:%S")
            if target <= now:
                return f"Target time {target_time} has passed, current time: {now.strftime('%Y-%m-%d %H:%M:%S')}"
        
        wait_seconds = (target - now).total_seconds()
        await asyncio.sleep(wait_seconds)
        return f"Reached {target_time}, current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    except ValueError as e:
        return f"Invalid time format: {e}"

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
