"""
商品详情查询工具
根据商品ID或商品名称查询详细信息，包括成分、营养、货架位置等。
"""

from typing import Optional
from langchain_core.tools import tool
from tools._data_loader import load_products, load_products_map


@tool
def get_product_detail(
        product_id: Optional[str] = None,
        product_name: Optional[str] = None,
) -> None | str:
    """查询商品详细信息。可通过商品ID精确查询，或通过商品名称模糊搜索。

    Args:
        product_id: 商品ID，如"DAIRY001""SNACK004"，精确匹配
        product_name: 商品名称关键词，如"酸奶""燕麦片"，模糊匹配

    Returns:
        商品详细信息，包括名称、品牌、规格、价格、描述、营养信息、货架位置等
    """
    if not product_id and not product_name:
        return "请提供商品ID或商品名称进行查询。"

    products_map = load_products_map()

    # 精确ID查询
    if product_id:
        product = products_map.get(product_id.upper())
        if not product:
            return f"未找到商品ID为 {product_id} 的商品。请检查ID是否正确。"
        return _format_detail(product)

    # 名称模糊搜索
    if product_name:
        all_products = load_products()
        matches = []
        search_lower = product_name.lower()
        for p in all_products:
            search_text = (p["name"] + " " + " ".join(p.get("tags", []))).lower()
            if search_lower in search_text:
                matches.append(p)

        if not matches:
            return f"未找到名称包含「{product_name}」的商品。"

        if len(matches) == 1:
            return _format_detail(matches[0])

        # 多个匹配时，返回列表让用户选择
        output = f"找到 {len(matches)} 个匹配商品，请确认您要查询哪一个：\n\n"
        for p in matches:
            output += (
                f"- 【{p['product_id']}】{p['name']} "
                f"({p['brand']}, {p['spec']}, ¥{p['price']})\n"
            )
        return output.strip()
    return None


def _format_detail(product: dict) -> str:
    """格式化商品详情"""
    stock_status = "✅ 有货" if product.get("in_stock", True) else "❌ 缺货"

    detail = (
        f"{'=' * 40}\n"
        f"商品名称：{product['name']}\n"
        f"商品ID：{product['product_id']}\n"
        f"{'=' * 40}\n"
        f"品类：{product['category']} > {product['sub_category']}\n"
        f"品牌：{product['brand']}\n"
        f"规格：{product['spec']}\n"
        f"价格：¥{product['price']}/{product['unit']}\n"
        f"库存状态：{stock_status}\n"
        f"货架位置：{product['shelf_location']}\n"
        f"\n"
        f"【商品描述】\n"
        f"{product['description']}\n"
    )

    if product.get("tags"):
        detail += f"\n【标签】{'、'.join(product['tags'])}\n"

    if product.get("nutrition_highlights"):
        detail += f"\n【营养亮点】\n{product['nutrition_highlights']}\n"

    return detail.strip()
