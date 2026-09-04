"""
门店信息查询工具
查询门店基本信息：营业时间、地址、设施、配送服务等。
"""

from langchain_core.tools import tool
from tools._data_loader import load_store_info


# 门店详细信息（静态数据，实际项目中可从数据库或配置文件读取）
_STORE_DETAILS = {
    "store_name": "鲜选生活超市（南山店）",
    "address": "深圳市南山区科技园南路88号万象天地B1层",
    "metro": "1号线高新园站A出口，步行约5分钟",
    "bus": "科技园南站（M222、M372、M530路）",
    "hours_weekday": "08:00 - 22:00",
    "hours_weekend": "07:30 - 22:30",
    "hours_holiday": "08:00 - 22:00（除夕 08:00 - 18:00）",
    "wifi": "连接 FreshMart-Guest，无需密码",
    "self_checkout": "出口处6台自助结账机，支持微信/支付宝/银行卡",
    "locker": "入口处免费储物柜，扫码存取",
    "baby_room": "B1层卫生间旁，配备哺乳椅、换尿布台、热水",
    "delivery_range": "门店周边3公里",
    "delivery_time": "30分钟达",
    "delivery_min_order": "29元",
    "delivery_fee": "3公里内5元，满79元免配送费",
    "delivery_hours": "09:00 - 21:00",
    "parking": "万象天地B2-B3层，购物满100元免费停2小时，满200元免费停4小时",
    "charging_station": "B2层8个新能源充电桩（4快充+4慢充）",
}


@tool
def get_store_info(
    query_type: str = "all",
) -> str:
    """查询门店信息。可查询营业时间、地址交通、服务设施、配送服务、停车信息等。

    Args:
        query_type: 查询类型，可选值：
            - "all": 全部信息
            - "hours": 营业时间
            - "address": 地址和交通
            - "facilities": 服务设施（WiFi、储物柜、母婴室等）
            - "delivery": 配送服务
            - "parking": 停车信息

    Returns:
        门店相关信息
    """
    info = _STORE_DETAILS

    if query_type == "hours":
        return (
            f"🕐 {info['store_name']} 营业时间\n"
            f"  周一至周五：{info['hours_weekday']}\n"
            f"  周六至周日：{info['hours_weekend']}\n"
            f"  法定节假日：{info['hours_holiday']}"
        )

    elif query_type == "address":
        return (
            f"📍 {info['store_name']} 地址与交通\n"
            f"  地址：{info['address']}\n"
            f"  地铁：{info['metro']}\n"
            f"  公交：{info['bus']}"
        )

    elif query_type == "facilities":
        return (
            f"🏪 {info['store_name']} 服务设施\n"
            f"  WiFi：{info['wifi']}\n"
            f"  自助结账：{info['self_checkout']}\n"
            f"  储物柜：{info['locker']}\n"
            f"  母婴室：{info['baby_room']}\n"
            f"  无障碍通道：全店覆盖"
        )

    elif query_type == "delivery":
        return (
            f"🚚 {info['store_name']} 配送服务\n"
            f"  配送范围：{info['delivery_range']}\n"
            f"  配送时效：{info['delivery_time']}\n"
            f"  起送金额：{info['delivery_min_order']}\n"
            f"  配送费：{info['delivery_fee']}\n"
            f"  配送时间：{info['delivery_hours']}"
        )

    elif query_type == "parking":
        return (
            f"🅿️ {info['store_name']} 停车信息\n"
            f"  停车场：{info['parking']}\n"
            f"  充电桩：{info['charging_station']}"
        )

    else:  # all
        return (
            f"🏪 {info['store_name']}\n"
            f"{'=' * 40}\n"
            f"📍 地址：{info['address']}\n"
            f"🚇 地铁：{info['metro']}\n"
            f"🚌 公交：{info['bus']}\n"
            f"\n"
            f"🕐 营业时间\n"
            f"  周一至周五：{info['hours_weekday']}\n"
            f"  周六至周日：{info['hours_weekend']}\n"
            f"  法定节假日：{info['hours_holiday']}\n"
            f"\n"
            f"🏪 服务设施\n"
            f"  WiFi：{info['wifi']}\n"
            f"  自助结账：{info['self_checkout']}\n"
            f"  储物柜：{info['locker']}\n"
            f"  母婴室：{info['baby_room']}\n"
            f"\n"
            f"🚚 配送服务\n"
            f"  范围：{info['delivery_range']} | 时效：{info['delivery_time']}\n"
            f"  起送：{info['delivery_min_order']} | 运费：{info['delivery_fee']}\n"
            f"\n"
            f"🅿️ 停车\n"
            f"  {info['parking']}\n"
            f"  充电桩：{info['charging_station']}"
        )