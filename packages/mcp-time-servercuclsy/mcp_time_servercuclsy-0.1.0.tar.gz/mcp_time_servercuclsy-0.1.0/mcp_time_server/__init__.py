from typing import Optional 
from datetime import datetime 
from mcp.server.fastmcp import FastMCP 

# 尝试导入 pytz 模块
try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False

# 初始化 FastMCP 服务器实例 
# 参数 "time-server" 是服务器的名称 
mcp = FastMCP("time-server") 


@mcp.tool() 
def get_current_time(timezone: Optional[str] = None) -> str: 
    """获取当前时间的工具函数 
    
    Args: 
        timezone: 可选参数，时区字符串，例如 "Asia/Shanghai"、"America/New_York" 
                  如果不提供，将使用系统默认时区 
    
    Returns: 
        格式化的当前时间字符串 
    """
    try: 
        if timezone:
            if PYTZ_AVAILABLE:
                # 如果提供了时区参数，使用指定的时区 
                tz = pytz.timezone(timezone) 
                current_time = datetime.now(tz) 
            else:
                return "错误：pytz 模块未安装，无法使用时区功能"
        else: 
            # 如果没有提供时区参数，使用系统默认时区 
            current_time = datetime.now() 
        
        # 格式化时间字符串 
        # 格式：YYYY-MM-DD HH:MM:SS.SSSSSS 时区名称 
        return current_time.strftime("%Y-%m-%d %H:%M:%S.%f %Z") 
    except pytz.exceptions.UnknownTimeZoneError: 
        # 处理无效的时区参数 
        return f"错误：未知的时区 '{timezone}'"


__all__ = ["mcp", "get_current_time"]
