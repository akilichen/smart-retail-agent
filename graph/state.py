"""
Agent 状态定义
定义 LangGraph 中流转的核心数据结构。
"""

from typing import List, Annotated, Optional, Any, TypedDict
# from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """Agent 全局状态，在 Graph 各节点间流转"""

    # 对话消息历史（自动追加，不会覆盖）
    messages: Annotated[List[BaseMessage], add_messages]

    # 意图分类结果："direct_reply" | "needs_tools"
    intent: Optional[str]

    # 购物车状态：记录用户已决定购买的商品ID列表
    cart: List[str]

    # 组合推荐是否已触发（每轮对话只触发一次）
    recommendation_triggered: bool
