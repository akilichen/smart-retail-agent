"""
工具模块统一导出
所有工具在此集中注册，供LangGraph Agent使用。
"""

from tools.search_products import search_products
from tools.get_product_detail import get_product_detail
from tools.get_promotions import get_promotions
from tools.get_store_info import get_store_info
from tools.get_faq import get_faq
from tools.get_bundled_recommendations import get_bundled_recommendations

# 所有工具的列表，直接传给 agent.bind_tools()
ALL_TOOLS = [
    search_products,
    get_product_detail,
    get_promotions,
    get_store_info,
    get_faq,
    get_bundled_recommendations,
]

__all__ = [
    "search_products",
    "get_product_detail",
    "get_promotions",
    "get_store_info",
    "get_faq",
    "get_bundled_recommendations",
    "ALL_TOOLS",
]