"""
LangGraph 编排层
包含：节点函数、条件路由、Graph 组装
"""

import json
from typing import Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from config import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    LLM_MODEL,
    LLM_TEMPERATURE,
    MAX_RECURSION_LIMIT,
)
from tools import ALL_TOOLS, get_bundled_recommendations
from graph.state import AgentState


# ============================================================
# LLM 实例
# ============================================================

def _create_llm(bind_tools: bool = True, disable_thinking: bool = True) -> ChatOpenAI:
    """创建 LLM 实例，可选是否绑定工具

    默认 disable_thinking=True：
    deepseek-flash v4 等支持 thinking 的模型在多轮 tool calling 场景下，
    thinking 模式会与 tool_choice 冲突（classify_intent），
    且要求 reasoning_content 显式回传（agent 节点），关闭更稳妥。
    """
    kwargs = {
        "model": LLM_MODEL,
        "temperature": LLM_TEMPERATURE,
        "api_key": OPENAI_API_KEY,
    }
    if OPENAI_BASE_URL:
        kwargs["base_url"] = OPENAI_BASE_URL
    if disable_thinking:
        kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
    llm = ChatOpenAI(**kwargs)
    if bind_tools:
        llm = llm.bind_tools(ALL_TOOLS)
    return llm


# Agent 系统提示词
_AGENT_SYSTEM_PROMPT = """你是"鲜选生活超市"的智能购物助手。你的职责是帮助顾客找到合适的商品、了解促销优惠、解答门店相关问题。

## 可用能力
- 搜索商品：支持自然语言描述（如"无糖饮料""火锅食材"）
- 查询商品详情：成分、营养、价格、货架位置
- 查询促销活动：满减、折扣、买赠等
- 查询门店信息：营业时间、地址、配送、停车等
- 检索FAQ：退换货政策、会员制度等
- 组合推荐：根据用户已选商品推荐搭配

## 行为准则
1. 当用户购买或浏览某类商品时，主动推荐关联搭配商品（如买酸奶→推荐燕麦、水果）
2. 推荐搭配时，同步告知可叠加的促销优惠，帮用户省钱
3. 回答简洁专业，商品信息用结构化格式呈现
4. 如果工具返回了多个结果，优先推荐性价比高的商品
5. 不确定时如实告知，不编造商品信息
"""

# 最终响应生成提示词
_RESPONSE_SYSTEM_PROMPT = """你是"鲜选生活超市"的智能购物助手。现在请根据对话历史和工具返回的结果，为用户生成最终回复。

## 回复要求
1. 如果工具返回了商品搜索结果，用简洁的列表格式呈现
2. 如果有组合推荐结果，自然地融入回复中，说明搭配理由
3. 如果有相关促销，主动告知用户可叠加的优惠
4. 回复简洁友好，不要太冗长
5. 不要重复工具已经返回的原始数据，用自然语言总结
"""


# ============================================================
# 节点函数
# ============================================================

class IntentSchema(BaseModel):
    """意图分类结果"""
    intent: Literal["direct_reply", "needs_tools"] = Field(
        description="direct_reply=打招呼/闲聊/告别等无需工具的对话; needs_tools=商品搜索/促销查询/门店信息/FAQ等需要调用工具的请求"
    )


def classify_intent(state: AgentState) -> dict:
    """
    节点1：意图分类
    判断用户消息是否需要调用工具。
    - direct_reply：打招呼、闲聊、告别 → 直接回复
    - needs_tools：商品搜索、促销查询、门店信息、FAQ等 → 需要工具
    """
    llm = _create_llm(bind_tools=False, disable_thinking=True)
    structured_llm = llm.with_structured_output(IntentSchema, method="function_calling")
    result = structured_llm.invoke(state["messages"])
    return {"intent": result.intent}


def agent(state: AgentState) -> dict:
    """
    节点2：Agent 核心推理
    调用绑定了工具的 LLM，决定是否调用工具以及调用哪些工具。
    """
    llm = _create_llm(bind_tools=True)

    messages = [SystemMessage(content=_AGENT_SYSTEM_PROMPT)] + state["messages"]
    response = llm.invoke(messages)

    return {"messages": [response]}


def tools_node(state: AgentState) -> dict:
    """
    节点3：工具执行
    执行 Agent 请求的工具调用，返回工具结果。
    """
    tool_node = ToolNode(ALL_TOOLS)
    return tool_node.invoke(state)


def check_recommendation(state: AgentState) -> dict:
    """
    节点4：组合推荐触发检查
    检查工具执行结果中是否涉及商品相关操作，决定是否触发组合推荐。
    """
    if state.get("recommendation_triggered", False):
        return {}

    messages = state["messages"]

    # 从后往前找最近的 ToolMessage，检查是否来自商品相关工具
    product_tools = {"search_products", "get_product_detail"}
    keyword = None

    for msg in reversed(messages):
        if isinstance(msg, ToolMessage) and msg.name in product_tools:
            # 找到触发该工具调用的 AI Message，提取参数
            for prev_msg in reversed(messages):
                if hasattr(prev_msg, "tool_calls") and prev_msg.tool_calls:
                    for tc in prev_msg.tool_calls:
                        if tc["name"] == msg.name:
                            args = tc["args"]
                            if isinstance(args, str):
                                try:
                                    args = json.loads(args)
                                except (json.JSONDecodeError, TypeError):
                                    args = {}
                            # 提取品类或搜索关键词
                            keyword = (
                                args.get("category")
                                or args.get("query")
                                or args.get("product_name")
                                or args.get("product_name_or_category")
                            )
                            break
                    break
            break

    # 如果从工具参数中没提取到，从用户消息中匹配品类关键词
    if not keyword:
        category_keywords = [
            "酸奶", "牛奶", "纯牛奶", "麦片", "坚果", "面包",
            "火锅", "火锅底料", "肥牛", "可乐", "碳酸饮料",
            "啤酒", "茶饮料", "方便面", "泡面", "水果",
            "草莓", "猫粮", "犬粮", "宠物",
        ]
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                for kw in category_keywords:
                    if kw in msg.content:
                        keyword = kw
                        break
                break

    if keyword:
        # 调用组合推荐工具
        rec_result = get_bundled_recommendations.invoke(
            {"product_name_or_category": keyword}
        )
        # 注意：必须用 AIMessage，不能用 ToolMessage。
        # ToolMessage 要求其 tool_call_id 必须对应当前 AIMessage 的某个 tool_call.id，
        # 而这里是我们自动触发的"额外"推荐，并无对应的 tool_call，
        # 直接用 ToolMessage + 假 id 会被 OpenAI API 400 拒绝。
        rec_text = rec_result if isinstance(rec_result, str) else str(rec_result)
        return {
            "messages": [
                AIMessage(
                    content=f"[系统自动追加的搭配推荐参考]\n{rec_text}",
                )
            ],
            "recommendation_triggered": True,
        }

    return {}


def generate_response(state: AgentState) -> dict:
    """
    节点5：最终响应生成
    使用不绑定工具的 LLM，根据对话历史生成最终回复。
    用于 direct_reply 场景（打招呼、闲聊等）。
    """
    llm = _create_llm(bind_tools=False)

    messages = [SystemMessage(content=_RESPONSE_SYSTEM_PROMPT)] + state["messages"]
    response = llm.invoke(messages)

    return {"messages": [response]}


# ============================================================
# 条件路由函数
# ============================================================

def route_from_start(state: AgentState) -> str:
    """
    从 START 出发的路由：根据意图分类结果决定走哪条路。
    - direct_reply → generate_response（直接回复，不调工具）
    - needs_tools → agent（进入工具调用循环）
    """
    intent = state.get("intent", "needs_tools")
    if intent == "direct_reply":
        return "generate_response"
    return "agent"


def route_after_agent(state: AgentState) -> str:
    """
    Agent 执行后的路由：检查是否有工具调用。
    - 有 tool_calls → tools（执行工具）
    - 无 tool_calls → END
    """
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def route_after_tools(state: AgentState) -> str:
    """
    工具执行后的路由：检查是否需要触发组合推荐。
    - 未触发过推荐 且 涉及商品操作 → check_recommendation
    - 否则 → agent（回到 Agent 生成响应）
    """
    if not state.get("recommendation_triggered", False):
        # 检查最近的 ToolMessage 是否来自商品相关工具
        product_tools = {"search_products", "get_product_detail"}
        for msg in reversed(state["messages"]):
            if isinstance(msg, ToolMessage):
                if msg.name in product_tools:
                    return "check_recommendation"
                break
    return "agent"


def route_after_recommendation(state: AgentState) -> str:
    """
    推荐检查后的路由：回到 Agent，让 Agent 结合推荐结果生成最终回复。
    """
    return "agent"


# ============================================================
# Graph 组装
# ============================================================

def build_graph():
    """
    构建并编译 LangGraph 状态图。

    节点：
    - classify_intent：意图分类
    - agent：核心推理（绑定工具）
    - tools：工具执行
    - check_recommendation：组合推荐触发检查
    - generate_response：最终响应生成（不绑定工具）

    返回编译后的 Graph，可直接 .invoke() 使用。
    """
    builder = StateGraph(AgentState)

    # === 注册节点 ===
    builder.add_node("classify_intent", classify_intent)
    builder.add_node("agent", agent)
    builder.add_node("tools", tools_node)
    builder.add_node("check_recommendation", check_recommendation)
    builder.add_node("generate_response", generate_response)

    # === 定义边 ===

    # START → 意图分类
    builder.add_edge(START, "classify_intent")

    # 意图分类 → 条件路由
    builder.add_conditional_edges(
        "classify_intent",
        route_from_start,
        {
            "agent": "agent",
            "generate_response": "generate_response",
        },
    )

    # Agent → 条件路由（有tool_calls → tools，否则 → END）
    builder.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "tools": "tools",
            END: END,
        },
    )

    # 工具执行 → 条件路由（需推荐 → check_recommendation，否则 → agent）
    builder.add_conditional_edges(
        "tools",
        route_after_tools,
        {
            "check_recommendation": "check_recommendation",
            "agent": "agent",
        },
    )

    # 推荐检查 → 回到 agent
    builder.add_conditional_edges(
        "check_recommendation",
        route_after_recommendation,
        {
            "agent": "agent",
        },
    )

    # 最终响应生成 → END
    builder.add_edge("generate_response", END)

    # === 编译 ===
    graph = builder.compile()
    return graph