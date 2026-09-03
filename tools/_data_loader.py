"""
共享数据加载器（内部模块）
所有工具通过此模块读取json数据，统一管理数据加载和缓存
"""
import json
import os.path
from typing import List, Dict, Any, Optional
from functools import lru_cache

# 项目根目录（tools/ 的上一级）
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@lru_cache(maxsize=1)
def load_products() -> List[Dict[str, Any]]:
    """
    加载商品数据，使用lru cache缓存，只读取一次
    :return:
    """
    filepath = os.path.join(_PROJECT_ROOT, 'data', 'products.json')
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['products']


@lru_cache(maxsize=1)
def load_products_map() -> Dict[str, Dict[str, Any]]:
    """加载商品数据并转为 {product_id: product} 的字典，方便按ID查找"""
    products = load_products()
    return {p["product_id"]: p for p in products}


@lru_cache(maxsize=1)
def load_promotions() -> List[Dict[str, Any]]:
    """加载促销数据"""
    filepath = os.path.join(_PROJECT_ROOT, 'data', 'promotions.json')
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['promotions']


@lru_cache(maxsize=1)
def load_bundles() -> List[Dict[str, Any]]:
    """加载搭配推荐规则"""
    filepath = os.path.join(_PROJECT_ROOT, 'data', 'bundles.json')
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['rules']


@lru_cache(maxsize=1)
def load_store_info() -> Dict[str, Any]:
    """加载门店元信息"""
    filepath = os.path.join(_PROJECT_ROOT, 'data', 'products.json')
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('metadata', {})

