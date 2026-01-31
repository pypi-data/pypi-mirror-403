#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价格结果数据模型
用于存储沃尔玛商品价格爬取结果
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class PriceResult:
    """价格结果数据模型

    Attributes:
        sku: 商品SKU
        original_price: 原价/当前价（无促销时的价格）
        promo_price: 促销价（有促销时显示的价格）
        status: 状态 - success | error | not_found
        error_message: 错误信息（status != success 时填充）
        detected_at: 检测时间
    """
    sku: str
    original_price: Optional[str] = None
    promo_price: Optional[str] = None
    status: str = "success"
    error_message: Optional[str] = None
    detected_at: datetime = field(default_factory=datetime.now)

    @property
    def display_price(self) -> str:
        """D列显示值（原价/当前价）"""
        if self.status != "success":
            return "获取异常"
        return self.original_price or "获取异常"

    @property
    def display_promo_price(self) -> str:
        """E列显示值（促销价）"""
        if self.status != "success":
            return "获取异常"
        return self.promo_price or ""

    @property
    def is_on_promotion(self) -> bool:
        """是否有促销"""
        return self.promo_price is not None and self.status == "success"

    @property
    def url(self) -> str:
        """生成商品URL"""
        return f"https://www.walmart.com/ip/{self.sku}"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "sku": self.sku,
            "original_price": self.original_price,
            "promo_price": self.promo_price,
            "status": self.status,
            "error_message": self.error_message,
            "detected_at": self.detected_at.isoformat(),
            "is_on_promotion": self.is_on_promotion,
            "url": self.url
        }

    def __repr__(self) -> str:
        if self.status != "success":
            return f"PriceResult(sku={self.sku}, status={self.status}, error={self.error_message})"
        if self.is_on_promotion:
            return f"PriceResult(sku={self.sku}, price={self.original_price}, promo={self.promo_price})"
        return f"PriceResult(sku={self.sku}, price={self.original_price})"
