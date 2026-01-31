#!/usr/bin/env python3
"""
计算器 MCP 服务 - 提供两个数相加的工具
"""
from typing import Any
from mcp.server.fastmcp import FastMCP

# 初始化 MCP 服务器，监听 0.0.0.0 方便外部访问
mcp = FastMCP("CalculatorServer")


@mcp.tool()
def add_numbers(a: float, b: float) -> str:
    """
    计算两个数字的和。

    Args:
        a: 第一个数字
        b: 第二个数字

    Returns:
        两个数字相加的结果
    """
    try:
        result = a + b
        return f"计算结果: {a} + {b} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


@mcp.tool()
def subtract_numbers(a: float, b: float) -> str:
    """
    计算两个数字的差（a - b）。

    Args:
        a: 被减数
        b: 减数

    Returns:
        两个数字相减的结果
    """
    try:
        result = a - b
        return f"计算结果: {a} - {b} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


@mcp.tool()
def multiply_numbers(a: float, b: float) -> str:
    """
    计算两个数字的乘积。

    Args:
        a: 第一个数字
        b: 第二个数字

    Returns:
        两个数字相乘的结果
    """
    try:
        result = a * b
        return f"计算结果: {a} × {b} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


@mcp.tool()
def divide_numbers(a: float, b: float) -> str:
    """
    计算两个数字的商（a / b）。

    Args:
        a: 被除数
        b: 除数

    Returns:
        两个数字相除的结果
    """
    try:
        if b == 0:
            return "错误: 除数不能为零"
        result = a / b
        return f"计算结果: {a} ÷ {b} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


def run() -> None:
    """启动 MCP 服务器（stdio 传输，stdout 仅用于 JSON-RPC，不可 print）"""
    mcp.run(transport="stdio")


def main() -> None:
    run()


if __name__ == "__main__":
    main()
