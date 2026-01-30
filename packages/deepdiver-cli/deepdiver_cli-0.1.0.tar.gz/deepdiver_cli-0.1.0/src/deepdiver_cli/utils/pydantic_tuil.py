from typing import Any, Dict

from openai import pydantic_function_tool


def parameters_from_input_model(cls) -> Dict[str, Any]:
    """根据 input_model 生成 LLM tool 的 parameters 声明。"""
    return pydantic_function_tool(cls)["function"]["parameters"]  # type: ignore
