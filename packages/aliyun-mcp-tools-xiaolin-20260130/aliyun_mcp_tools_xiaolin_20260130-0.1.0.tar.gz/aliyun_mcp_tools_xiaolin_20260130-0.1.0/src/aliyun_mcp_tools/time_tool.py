"""Time tool module."""

import datetime

def get_current_time() -> dict:
    """
    获取当前系统时间
    """
    try:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {"success": True, "time": current_time}
    except Exception as e:
        return {"success": False, "error": str(e)}
