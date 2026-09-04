"""
促销查询工具
查询当前生效的促销活动，支持按商品ID、品类或全量查询。
"""

from typing import Optional, List
from langchain_core.tools import tool
from tools._data_loader import load_promotions, load_products_map


@tool
def get_promotions(
    product_id: Optional[str] = None,
    category: Optional[str] = None,
) -> str:
    """查询当前生效的促销活动。可按商品ID查询该商品参与的促销，或按品类查询，或不传参数查看全部促销。

    Args:
        product_id: 商品ID，如"DAIRY001"，查询该商品参与的所有促销活动
        category: 品类名称，如"乳制品""饮料"，查询该品类下的所有促销

    Returns:
        当前生效的促销活动列表，包含活动类型、优惠内容、适用商品等
    """
    promotions = load_promotions()
    products_map = load_products_map()

    matched_promos: List[dict] = []

    if product_id:
        # 按商品ID查询
        product = products_map.get(product_id.upper())
        if not product:
            return f"未找到商品ID为 {product_id} 的商品。"

        for promo in promotions:
            if product_id.upper() in promo.get("applicable_products", []):
                matched_promos.append(promo)

        if not matched_promos:
            return f"商品「{product['name']}」（{product_id}）当前没有参与任何促销活动。"

        output = f"商品「{product['name']}」当前参与的促销活动：\n\n"
        for promo in matched_promos:
            output += _format_promo(promo, products_map) + "\n\n"
        return output.strip()

    elif category:
        # 按品类查询
        for promo in promotions:
            # 检查促销的applicable_products中是否有该品类的商品
            for pid in promo.get("applicable_products", []):
                p = products_map.get(pid)
                if p and p["category"] == category:
                    matched_promos.append(promo)
                    break

        if not matched_promos:
            return f"品类「{category}」当前没有促销活动。"

        output = f"品类「{category}」当前的促销活动：\n\n"
        for promo in matched_promos:
            output += _format_promo(promo, products_map) + "\n\n"
        return output.strip()

    else:
        # 查看全部促销
        if not promotions:
            return "当前没有生效的促销活动。"

        output = f"当前共有 {len(promotions)} 个促销活动：\n\n"
        for promo in promotions:
            output += _format_promo(promo, products_map) + "\n\n"
        return output.strip()


def _format_promo(promo: dict, products_map: dict) -> str:
    """格式化促销信息"""
    type_emoji = {
        "满减": "💰",
        "折扣": "🏷️",
        "买赠": "🎁",
        "特价": "🔥",
        "第二件半价": "½",
        "满赠": "🎁",
        "组合优惠": "📦",
    }
    emoji = type_emoji.get(promo["type"], "📌")

    # 获取适用商品名称
    applicable_names = []
    for pid in promo.get("applicable_products", []):
        p = products_map.get(pid)
        if p:
            applicable_names.append(p["name"])

    output = (
        f"{emoji} [{promo['type']}] {promo['title']}\n"
        f"  说明：{promo['description']}\n"
        f"  是否可叠加：{'是' if promo.get('stackable') else '否'}\n"
        f"  适用商品（{len(promo.get('applicable_products', []))}个）："
        f"{'、'.join(applicable_names[:5])}"
    )
    if len(applicable_names) > 5:
        output += f"等{len(applicable_names)}个商品"

    return output