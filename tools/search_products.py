"""
商品搜搜工具
支持两种搜索工具
1、语义搜索： 通过向量检索找到语义相关的商品（如健康零食、坚果、燕麦）
2、条件过滤：按品类、价格区间、品牌等结构化条件筛选

agent可根据用户意图灵活的组合使用
"""

from typing import Optional, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.tools import tool

import os

from config import (
    EMBEDDING_MODEL,
    OPENAI_GJLD_API_KEY,
    OPENAI_GJLD_BASE_URL,
    CHROMA_PERSIST_DIR,
    CHROMA_COLLECTION_PRODUCTS,
)
from tools._data_loader import load_products_map


def _get_products_vectorstore() -> Chroma:
    """获得商品向量库实例"""
    embed_kwargs = {"model": EMBEDDING_MODEL, "api_key": OPENAI_GJLD_API_KEY}
    if OPENAI_GJLD_BASE_URL:
        embed_kwargs["base_url"] = OPENAI_GJLD_BASE_URL
    embeddings = OpenAIEmbeddings(**embed_kwargs)

    return Chroma(
        persist_directory=os.path.join(CHROMA_PERSIST_DIR, "products"),
        collection_name=CHROMA_COLLECTION_PRODUCTS,
        embedding_function=embeddings
    )


def _format_product(product: Dict[str, Any]) -> str:
    """格式化单个商品信息为可读文本"""
    stock_status = "有货" if product.get("in_stock", True) else "缺货"
    return (
        f"【{product['product_id']}】{product['name']}\n"
        f"  品类：{product['category']} > {product['sub_category']} | "
        f"品牌：{product['brand']} | 规格：{product['spec']}\n"
        f"  价格：¥{product['price']}/{product['unit']} | 库存：{stock_status}\n"
        f"  货架：{product['shelf_location']}\n"
        f"  简介：{product['description']}"
    )


@tool
def search_products(
        query: str,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        brand: Optional[str] = None,
        in_stock_only: bool = True,
        top_k: int = 5,

) -> str:
    """
    搜索商超商品。支持自然语言搜索（如无糖饮料，健康食品）和结构化条件筛选

    Args:
        query: 搜索关键词或自然语言描述，如"无糖可乐""适合早餐的麦片""火锅食材"
        category: 按品类筛选，可选值：乳制品、休闲食品、饮料、水果、肉禽蛋、蔬菜、烘焙、调味品、方便食品、冷冻食品、母婴用品、家居清洁、酒水、宠物用品
        min_price: 最低价格（元）
        max_price: 最高价格（元）
        brand: 按品牌筛选，如"蒙牛""伊利""乐事"
        in_stock_only: 是否只显示有货商品，默认True
        top_k: 返回结果数量，默认5

    Returns:
        匹配的商品列表，包含名称、价格、规格、货架位置等信息
    """
    results = []

    # === 策略1： 如果有自然语言query， 使用向量语义检索===
    if query and query.strip():
        try:
            vs = _get_products_vectorstore()
            # 构建过滤条件
            filter_conditions = {}
            if category:
                filter_conditions["category"] = category
            if brand:
                filter_conditions["brand"] = brand
            if in_stock_only:
                filter_conditions["in_stock"] = True

            search_kwargs = {"k": top_k * 2}  # 多筛选一些，后续做条件过滤
            if filter_conditions:
                search_kwargs["filter"] = filter_conditions

            docs = vs.similarity_search(query, **search_kwargs)

            products_map = load_products_map()
            for doc in docs:
                pid = doc.metadata.get("product_id")
                if pid and pid in products_map:
                    results.append(products_map[pid])
        except Exception as e:
            # 向量检索失败时降级为纯条件过滤
            pass

    # 策略2: 条件过滤（metadata过滤），可做独立或补充使用
    if not results:
        from tools._data_loader import load_products
        all_products = load_products()

        for p in all_products:
            # 品类过滤
            if category and p["category"] != category:
                continue
            if brand and p["brand"] != brand:
                continue
            if in_stock_only and p.get("in_stock", True):
                continue
            if min_price is not None and p["price"] < min_price:
                continue
            if max_price is not None and p["price"] > max_price:
                continue
            # keyword filter
            if query and query.strip():
                search_text = (
                        p["name"] + p["description"] +
                        " ".join(p.get("tags", [])) +
                        p["sub_category"]
                ).lower()
                if query.lower() not in search_text:
                    continue

            results.append(p)

    # === 对结果做价格过滤（向量检索结果也需要） ===
    if min_price is not None:
        results = [p for p in results if p["price"] >= min_price]
    if max_price is not None:
        results = [p for p in results if p["price"] <= max_price]

    # 按 product_id 去重
    seen = set()
    unique_results = []
    for p in results:
        if p["product_id"] not in seen:
            unique_results.append(p)

    results = unique_results[:top_k]

    # 格式化输出
    if not results:
        return f"未找到匹配「{query}」的商品。您可以尝试换个关键词或放宽筛选条件。"

    output = f"找到 {len(results)} 个匹配商品：\n\n"
    for p in results:
        output += _format_product(p) + "\n\n"

    return output.strip()
