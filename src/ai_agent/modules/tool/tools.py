from ai_agent.modules.tool.base import Tool


class GetTimeTool(Tool):
    """获取实时时间"""
    name = "get_current_time"
    description = "获取实时时间"

    def execute(self, **kwargs) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class CalculatorTool(Tool):
    """四则运算"""
    name = "calculator"
    description = "四则运算"

    @property
    def args(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "第一个数字"},
                "b": {"type": "number", "description": "第二个数字"},
                "op": {"type": "string", "description": "运算符"},
            },
            "required": ["a", "b", "op"]
        }

    def execute(self, **kwargs) -> str:
        a = kwargs["a"]
        b = kwargs["b"]
        op = kwargs["op"]
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            return a / b
        return "error"