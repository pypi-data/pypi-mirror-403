"""Calculator tool module."""

def calculator(python_expression: str) -> dict:
    """
    用于数学计算时，请始终使用此工具来计算 Python 表达式的结果。
    可以使用 `math` 和 `random` 模块。
    """
    try:
        result = eval(python_expression)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
