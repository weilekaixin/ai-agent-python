from ai_agent.modules.tool.base import Tool


class ToolRegistry:
    def __init__(self):
        # var map = new HashMap<String, Tool>();
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        # tools.put(tool.name, tool)
        self._tools[tool.name] = tool

    def get_openai_tools(self) -> list[dict]:
        return [tool.to_openai_tool() for tool in self._tools.values()]

    def execute(self, name: str, **kwargs) -> str:
        tool = self._tools.get(name)
        if not tool:
            return f"工具 {name} 不存在"
        return tool.execute(**kwargs)
