from aiogram.filters.callback_data import CallbackData


class NavCallbackData(CallbackData, prefix="nav"):  # navigate menu
    to: str


class BoolCd(CallbackData, prefix="bool"):
    req: str
    res: bool
    xtr: int | str | None = None


flags = {
    "RUB": "🇷🇺",
    "THB": "🇹🇭",
    "IDR": "🇮🇩",
    "TRY": "🇹🇷",
    "GEL": "🇬🇪",
    "VND": "🇻🇳",
    "AED": "🇦🇪",
    "AMD": "🇦🇲",
    "AZN": "🇦🇿",
    "CNY": "🇨🇳",
    "EUR": "🇪🇺",
    "HKD": "🇭🇰",
    "INR": "🇮🇳",
    "PHP": "🇵🇭",
    "USD": "🇺🇸",
}

cur_symbols = {
    1: "₽",
    2: "$",
    3: "€",
    7: "฿",
    8: "Rp",
    9: "₺",
    13: "₸",
    10: "₾",
    17: "₫",
    6: "🇦🇪",
    21: "֏",
    20: "₼",
    5: "¥",
    4: "$",
    12: "₹",
    14: "₱",
    33: "₴",
}
