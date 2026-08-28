"""
数据校验脚本：检查所有模拟数据的完整性和一致性
运行方式：python data/validate_data.py
"""

import json
import os


def validate_products():
    """校验商品数据"""
    print("=" * 50)
    print("🛒 校验商品数据...")

    with open("data/products.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    products = data["products"]
    print(f"   商品总数: {len(products)}")

    # 检查必填字段
    required_fields = ["product_id", "name", "category", "sub_category", "brand",
                       "spec", "price", "unit", "shelf_location", "description",
                       "tags", "in_stock"]
    errors = []
    for p in products:
        for field in required_fields:
            if field not in p:
                errors.append(f"商品 {p.get('product_id', '?')} 缺少字段: {field}")

    # 检查product_id唯一性
    ids = [p["product_id"] for p in products]
    if len(ids) != len(set(ids)):
        errors.append("存在重复的product_id")

    # 按品类统计
    categories = {}
    for p in products:
        cat = p["category"]
        categories[cat] = categories.get(cat, 0) + 1

    print(f"   品类分布:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"     {cat}: {count}个SKU")

    if errors:
        print(f"   ❌ 发现 {len(errors)} 个错误:")
        for e in errors:
            print(f"     - {e}")
    else:
        print(f"   ✅ 商品数据校验通过")

    return products, errors


def validate_promotions(products):
    """校验促销数据"""
    print("=" * 50)
    print("🏷️  校验促销数据...")

    with open("data/promotions.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    promos = data["promotions"]
    print(f"   促销活动总数: {len(promos)}")

    product_ids = {p["product_id"] for p in products}
    errors = []

    for promo in promos:
        print(f"   [{promo['promo_id']}] {promo['type']} - {promo['title']}")
        for pid in promo.get("applicable_products", []):
            if pid not in product_ids:
                errors.append(f"促销 {promo['promo_id']} 引用了不存在的商品: {pid}")

    if errors:
        print(f"   ❌ 发现 {len(errors)} 个错误:")
        for e in errors:
            print(f"     - {e}")
    else:
        print(f"   ✅ 促销数据校验通过")

    return errors


def validate_bundles(products):
    """校验搭配推荐数据"""
    print("=" * 50)
    print("🎁 校验搭配推荐数据...")

    with open("data/bundles.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    rules = data["rules"]
    print(f"   搭配规则总数: {len(rules)}")

    product_ids = {p["product_id"] for p in products}
    errors = []

    for rule in rules:
        rec_count = len(rule.get("recommendations", []))
        print(f"   [{rule['rule_id']}] {rule['trigger_category']} → {rec_count}个推荐")

        # 检查trigger_products
        for pid in rule.get("trigger_products", []):
            if pid not in product_ids:
                errors.append(f"规则 {rule['rule_id']} 的trigger引用了不存在的商品: {pid}")

        # 检查recommendations中的product_id
        for rec in rule.get("recommendations", []):
            if rec["product_id"] not in product_ids:
                errors.append(f"规则 {rule['rule_id']} 的推荐引用了不存在的商品: {rec['product_id']}")

    if errors:
        print(f"   ❌ 发现 {len(errors)} 个错误:")
        for e in errors:
            print(f"     - {e}")
    else:
        print(f"   ✅ 搭配推荐数据校验通过")

    return errors


def validate_faq():
    """校验FAQ文档"""
    print("=" * 50)
    print("📚 校验FAQ文档...")

    faq_dir = "faq"
    if not os.path.exists(faq_dir):
        print(f"   ❌ FAQ目录不存在: {faq_dir}")
        return ["FAQ目录不存在"]

    md_files = [f for f in os.listdir(faq_dir) if f.endswith(".md")]
    print(f"   FAQ文档数: {len(md_files)}")

    errors = []
    for f in sorted(md_files):
        filepath = os.path.join(faq_dir, f)
        size = os.path.getsize(filepath)
        with open(filepath, "r", encoding="utf-8") as fp:
            content = fp.read()
            lines = len(content.split("\n"))
        print(f"   [{f}] {size}字节, {lines}行")
        if size < 50:
            errors.append(f"{f} 文件内容过少（{size}字节）")

    if errors:
        print(f"   ❌ 发现 {len(errors)} 个错误")
    else:
        print(f"   ✅ FAQ文档校验通过")

    return errors


def main():
    print("🔍 开始数据校验...\n")

    all_errors = []

    products, errors = validate_products()
    all_errors.extend(errors)

    errors = validate_promotions(products)
    all_errors.extend(errors)

    errors = validate_bundles(products)
    all_errors.extend(errors)

    errors = validate_faq()
    all_errors.extend(errors)

    print("\n" + "=" * 50)
    if all_errors:
        print(f"❌ 数据校验完成，共发现 {len(all_errors)} 个问题")
    else:
        print("🎉 全部数据校验通过！可以进入Phase 2了")


if __name__ == "__main__":
    main()