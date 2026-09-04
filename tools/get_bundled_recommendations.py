"""
组合推荐工具（Bundle Recommendation）
核心功能：当用户购买或浏览某类商品时，推荐关联搭配商品，提升客单价。
匹配逻辑：按品类关键词匹配触发规则，返回推荐商品及推荐理由。
"""

from typing import Optional
from langchain_core.tools import tool
from tools._data_loader import load_bundles, load_products_map, load_promotions


@tool
def get_bundled_recommendations(
    product_name_or_category: str,
    product_id: Optional[str] = None,
) -> str:
    """查询商品搭配推荐。当用户购买了某类商品、或购物清单中包含某类商品时，
    调用此工具获取关联搭配推荐，用于提升客单价和购物体验。

    典型使用场景：
    - 用户买了酸奶 → 推荐燕麦片、坚果、水果
    - 用户买了火锅底料 → 推荐肥牛、虾滑、金针菇
    - 用户买了面包 → 推荐牛奶、咖啡

    Args:
        product_name_or_category: 商品名称或品类关键词，如"酸奶""火锅底料""面包"
        product_id: 可选，具体商品ID。如果提供，会优先按商品ID匹配规则

    Returns:
        搭配推荐列表，包含推荐商品信息和推荐理由
    """
    rules = load_bundles()
    products_map = load_products_map()
    promotions = load_promotions()

    matched_rule = None
    search_text = product_name_or_category.lower()

    # 策略1：如果提供了product_id，优先按ID匹配
    if product_id:
        product_id_upper = product_id.upper()
        for rule in rules:
            if product_id_upper in rule.get("trigger_products", []):
                matched_rule = rule
                break

    # 策略2：按关键词匹配
    if not matched_rule:
        for rule in rules:
            # 检查品类名匹配
            if rule["trigger_category"].lower() in search_text:
                matched_rule = rule
                break
            # 检查关键词匹配
            for keyword in rule.get("trigger_keywords", []):
                if keyword.lower() in search_text:
                    matched_rule = rule
                    break
            if matched_rule:
                break

    if not matched_rule:
        return f"暂无与「{product_name_or_category}」相关的搭配推荐。"

    # 构建推荐结果
    recommendations = matched_rule.get("recommendations", [])
    if not recommendations:
        return f"「{matched_rule['trigger_category']}」暂无搭配推荐。"

    # 获取触发商品信息
    trigger_info = ""
    if product_id and product_id.upper() in products_map:
        trigger_product = products_map[product_id.upper()]
        trigger_info = f"您选购的「{trigger_product['name']}」（¥{trigger_product['price']}）\n"
    else:
        trigger_info = f"基于「{matched_rule['trigger_category']}」类商品\n"

    output = f"🛒 {trigger_info}为您推荐以下搭配商品：\n\n"

    for i, rec in enumerate(recommendations, 1):
        pid = rec["product_id"]
        product = products_map.get(pid)
        if not product:
            continue

        stock_icon = "✅" if product.get("in_stock", True) else "❌缺货"
        output += (
            f"  {i}. {stock_icon} {product['name']}\n"
            f"     ¥{product['price']}/{product['unit']} | "
            f"{product['brand']} | {product['spec']}\n"
            f"     💡 {rec['reason']}\n\n"
        )

    # 检查是否有可叠加的促销
    applicable_promos = []
    trigger_products = matched_rule.get("trigger_products", [])
    for promo in promotions:
        promo_products = set(promo.get("applicable_products", []))
        # 检查促销是否同时覆盖触发商品和推荐商品
        rec_product_ids = {r["product_id"] for r in recommendations}
        if trigger_products and promo_products & set(trigger_products):
            if promo.get("stackable", False):
                applicable_promos.append(promo)

    if applicable_promos:
        output += "🏷️ 搭配购买可享受以下优惠：\n"
        for promo in applicable_promos:
            output += f"  - {promo['title']}：{promo['description']}\n"

    return output.strip()