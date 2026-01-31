"""Text processing tool module."""

def process_text(text: str, operation: str) -> dict:
    """
    文本处理工具
    参数：
    text: 要处理的文本
    operation: 操作类型，可以是 "uppercase", "lowercase", "capitalize", "count_words"
    """
    try:
        if operation == "uppercase":
            result = text.upper()
        elif operation == "lowercase":
            result = text.lower()
        elif operation == "capitalize":
            result = text.capitalize()
        elif operation == "count_words":
            result = len(text.split())
        else:
            return {"success": False, "error": "不支持的操作类型"}
        
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
