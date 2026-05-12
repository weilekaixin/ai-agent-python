from abc import ABC, abstractmethod


class Tool(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @property
    def args(self) -> dict:
        return {
            # 数据结构
            "type": "object",
            # 具体参数注释
            "properties": {},
            # 必填参数名称
            "required": []
        }

    @abstractmethod
    def execute(self, **kwargs) -> str:
        ...

    def to_openai_tool(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.args,
            }
        }
