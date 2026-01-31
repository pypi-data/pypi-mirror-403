from . import mcp

def main():
    """主函数，启动 MCP 服务器"""
    # 使用 streamable-http 传输方式运行服务器
    # 这种方式适用于基于 HTTP 的服务器发送事件
    print("MCP Time Server started with streamableHttp transport")
    print("Available tool: get_current_time")
    print("Ready to receive requests...")
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()