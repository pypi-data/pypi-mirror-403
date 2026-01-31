#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Walmart 价格监控爬虫
实现沃尔玛商品价格提取功能（带完整的反爬处理）
"""

import re
import time
import logging
from typing import List, Optional

from .base_spider import BaseSpider
from .walmart_bot_handler import WalmartBotHandler, BotDetectionType
from app.selectors.walmart_selectors import WalmartSelectors, WalmartTimeouts
from app.models.price_result import PriceResult

logger = logging.getLogger(__name__)


class WalmartPriceSpider(BaseSpider):
    """Walmart 价格监控爬虫

    实现功能：
    - 商品价格提取（当前价/促销价）
    - 促销状态检测（划线价识别）
    - 页面状态检测（404/下架）
    - 防爬验证处理（Logo点击、验证码等）

    注意：虽然参数名为 sku，但实际接收的是商品ID（10-13位长数字），
    用于构建 URL: https://www.walmart.com/ip/{商品ID}
    """

    # Walmart 商品 URL 模板
    PRODUCT_URL_TEMPLATE = "https://www.walmart.com/ip/{sku}"

    def __init__(self, user_data_path: str = None, concurrency: int = 1):
        # 不需要 terminal_ui，简化初始化
        super().__init__(user_data_path, terminal_ui=None, concurrency=concurrency)
        self.selectors = WalmartSelectors

        # 初始化防爬处理器（延迟初始化，因为 page 可能还没准备好）
        self._bot_handler = None

    @property
    def bot_handler(self) -> WalmartBotHandler:
        """获取防爬处理器（延迟初始化）"""
        if self._bot_handler is None:
            self._bot_handler = WalmartBotHandler(
                page=self.page,
                terminal_ui=self.terminal_ui
            )
        return self._bot_handler

    def _get_site_config(self, url: str) -> dict:
        """获取站点配置（实现基类抽象方法）"""
        return {
            'zip_code': '10001',
            'country': 'US',
            'homepage': 'https://www.walmart.com/',
            'currency': 'USD'
        }

    def check_product_page(self, url: str) -> dict:
        """检查单个商品页面（实现基类抽象方法，兼容接口）"""
        # 从 URL 提取 SKU
        sku = self._extract_sku_from_url(url)
        if not sku:
            return {
                "url": url,
                "result": -1,
                "status": "error",
                "error": "无法从URL提取SKU"
            }

        result = self.get_price(sku)
        return {
            "url": url,
            "sku": result.sku,
            "result": 1 if result.status == "success" else -1,
            "status": result.status,
            "price": result.original_price,
            "promo_price": result.promo_price,
            "error": result.error_message
        }

    def _extract_sku_from_url(self, url: str) -> Optional[str]:
        """从 URL 提取 SKU"""
        # 匹配 walmart.com/ip/XXXXXX 格式
        match = re.search(r'/ip/(\d+)', url)
        if match:
            return match.group(1)
        return None

    def get_price(self, sku: str) -> PriceResult:
        """获取单个商品的价格信息（带完整的防爬处理）

        Args:
            sku: 商品ID（10-13位长数字，来自钉钉表格A列）

        Returns:
            PriceResult: 价格结果
        """
        url = self.PRODUCT_URL_TEMPLATE.format(sku=sku)

        try:
            logger.info(f"获取价格: SKU={sku}")
            self.page.get(url)

            # 等待页面加载
            logger.debug("等待页面DOM加载...")
            self.page.wait.doc_loaded(timeout=WalmartTimeouts.PAGE_LOAD)
            time.sleep(WalmartTimeouts.NORMAL)

            # ✅ 关键改进1：使用防爬处理器检测和处理验证
            self._bot_handler = WalmartBotHandler(
                page=self.page,
                terminal_ui=self.terminal_ui
            )

            detection_type = self.bot_handler.detect()
            if detection_type != BotDetectionType.NONE:
                logger.info(f"检测到防爬验证: {detection_type.value}")
                if not self.bot_handler.handle(detection_type):
                    return PriceResult(
                        sku=sku,
                        status="error",
                        error_message=f"防爬验证未通过: {detection_type.value}"
                    )
                # 验证通过后等待页面稳定
                time.sleep(WalmartTimeouts.NORMAL)

            # 检查页面状态
            page_status = self._check_page_status()
            if page_status != "ok":
                logger.warning(f"页面状态异常: {page_status}")
                return PriceResult(
                    sku=sku,
                    status="error" if page_status == "error" else "not_found",
                    error_message=page_status
                )

            # ✅ 关键改进2：使用带重试的价格提取
            return self._extract_price_with_retry(sku)

        except Exception as e:
            logger.error(f"获取价格失败 SKU={sku}: {e}")
            return PriceResult(
                sku=sku,
                status="error",
                error_message=str(e)
            )

    def _check_page_status(self) -> str:
        """检查页面状态

        Returns:
            str: "ok" | "not_found" | "unavailable" | "error"
        """
        try:
            # 检查 404 页面
            not_found_selectors = [
                self.selectors.PageStatus.NOT_FOUND,
                self.selectors.PageStatus.NOT_FOUND_ALT
            ]
            for selector in not_found_selectors:
                if self.page.ele(selector, timeout=WalmartTimeouts.QUICK):
                    return "页面不存在"

            # 检查商品下架
            for selector in self.selectors.Stock.ALL_UNAVAILABLE:
                if self.page.ele(selector, timeout=WalmartTimeouts.QUICK):
                    return "商品不可用"

            # 检查是否有商品标题（确认页面加载正确）
            if not self.page.ele(self.selectors.PageStatus.PRODUCT_TITLE, timeout=WalmartTimeouts.SHORT):
                if not self.page.ele(self.selectors.PageStatus.PRODUCT_TITLE_ALT, timeout=WalmartTimeouts.SHORT):
                    return "页面结构异常"

            return "ok"

        except Exception as e:
            logger.error(f"检查页面状态失败: {e}")
            return "error"

    def _extract_price_with_retry(self, sku: str, max_retries: int = 3) -> PriceResult:
        """✅ 关键改进3：带重试机制的价格提取

        每次重试前滚动页面，模拟人类行为并触发懒加载

        Args:
            sku: 商品ID（参数名为 sku 但实际是商品ID）
            max_retries: 最大重试次数

        Returns:
            PriceResult: 价格结果
        """
        for attempt in range(max_retries):
            logger.debug(f"价格提取尝试 {attempt + 1}/{max_retries}")

            # 每次重试前滚动页面（模拟人类行为，触发懒加载）
            if attempt > 0:
                logger.debug("滚动页面触发懒加载...")
                self.page.scroll.to_half()
                time.sleep(1)
                self.page.scroll.to_top()
                time.sleep(1)

            # 尝试提取价格
            result = self._extract_price_info(sku)

            # 如果成功获取价格，直接返回
            if result.status == "success" and result.original_price:
                return result

            logger.debug(f"第 {attempt + 1} 次尝试未获取到价格")
            time.sleep(1)

        logger.warning(f"SKU={sku} 经过 {max_retries} 次尝试仍未获取到价格")
        return PriceResult(
            sku=sku,
            status="error",
            error_message="无法提取价格"
        )

    def _extract_price_info(self, sku: str) -> PriceResult:
        """提取价格信息

        检测逻辑：
        1. 先查找划线价（strike-through-price）
        2. 如果存在划线价，说明有促销
           - 原价 = 划线价
           - 促销价 = hero-price（去掉 "Now " 前缀）
        3. 如果不存在划线价，说明无促销
           - 当前价 = hero-price
           - 促销价 = None

        Args:
            sku: 商品ID（参数名为 sku 但实际是商品ID）

        Returns:
            PriceResult: 价格结果
        """
        try:
            # 1. 检查是否有划线价（判断是否有促销）
            strike_price = self._get_strike_through_price()

            # 2. 获取当前显示价格（hero-price）
            current_price = self._get_current_price()

            if strike_price:
                # 有促销：原价=划线价，促销价=当前价
                logger.info(f"SKU={sku} 有促销: 原价={strike_price}, 促销价={current_price}")
                return PriceResult(
                    sku=sku,
                    original_price=strike_price,
                    promo_price=current_price,
                    status="success"
                )
            elif current_price:
                # 无促销：只有当前价
                logger.info(f"SKU={sku} 无促销: 当前价={current_price}")
                return PriceResult(
                    sku=sku,
                    original_price=current_price,
                    promo_price=None,
                    status="success"
                )
            else:
                # 价格提取失败
                logger.warning(f"SKU={sku} 无法提取价格")
                return PriceResult(
                    sku=sku,
                    status="error",
                    error_message="无法提取价格"
                )

        except Exception as e:
            logger.error(f"提取价格信息失败: {e}")
            return PriceResult(
                sku=sku,
                status="error",
                error_message=str(e)
            )

    def _get_current_price(self) -> Optional[str]:
        """获取当前价格（hero-price）

        Returns:
            Optional[str]: 价格字符串，如 "$224.63"
        """
        for selector in self.selectors.Price.ALL_CURRENT_PRICE:
            try:
                element = self.page.ele(selector, timeout=WalmartTimeouts.SHORT)
                if element:
                    price_text = element.text
                    if price_text:
                        # 清理价格文本（移除 "Now " 等前缀）
                        price = self._clean_price_text(price_text)
                        # ✅ 添加价格格式验证（与划线价保持一致）
                        if price and self._is_valid_price(price):
                            logger.debug(f"找到当前价格: {price} (选择器: {selector})")
                            return price
                        elif price:
                            logger.debug(f"跳过无效价格格式: {price}")
            except Exception as e:
                logger.debug(f"选择器 {selector} 失败: {e}")
                continue

        return None

    def _get_strike_through_price(self) -> Optional[str]:
        """获取划线价（原价）

        Returns:
            Optional[str]: 价格字符串，如 "$299.99"，无促销返回 None
        """
        for selector in self.selectors.Price.ALL_ORIGINAL_PRICE:
            try:
                element = self.page.ele(selector, timeout=WalmartTimeouts.SHORT)
                if element:
                    price_text = element.text
                    if price_text:
                        price = self._clean_price_text(price_text)
                        # ✅ 关键修复：验证是否为有效价格格式
                        if price and self._is_valid_price(price):
                            logger.debug(f"找到划线价: {price} (选择器: {selector})")
                            return price
                        elif price:
                            logger.debug(f"跳过无效价格格式: {price}")
            except Exception as e:
                logger.debug(f"选择器 {selector} 失败: {e}")
                continue

        return None

    def _clean_price_text(self, text: str) -> Optional[str]:
        """清理价格文本

        处理各种格式：
        - "$224.63"
        - "Now $224.63"
        - "Was $299.99"
        - "$1,234.56"

        Args:
            text: 原始价格文本

        Returns:
            Optional[str]: 清理后的价格字符串，如 "$224.63"
        """
        if not text:
            return None

        text = text.strip()

        # 移除常见前缀
        prefixes = ['Now ', 'Was ', 'From ', 'Price: ']
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):]

        # 提取价格（$X,XXX.XX 格式）
        match = re.search(r'\$[\d,]+\.?\d*', text)
        if match:
            return match.group(0)

        return None

    def _is_valid_price(self, price: str) -> bool:
        """验证价格格式是否有效

        Args:
            price: 价格字符串（如 "$224.63"）

        Returns:
            bool: 是否为有效价格
        """
        if not price:
            return False

        # 价格必须以 $ 开头
        if not price.startswith('$'):
            return False

        # 提取数字部分
        price_value = price.replace('$', '').replace(',', '')

        try:
            value = float(price_value)
            # 价格必须大于0且小于100000（沃尔玛商品价格合理范围）
            return 0 < value < 100000
        except ValueError:
            return False

    def run(self, sku_list: List[str], data_source: str = "dingtalk") -> List[PriceResult]:
        """批量获取价格

        Args:
            sku_list: 商品ID列表（参数名为 sku_list 但实际是商品ID列表）
            data_source: 数据来源标识

        Returns:
            List[PriceResult]: 价格结果列表
        """
        if not sku_list:
            logger.warning("SKU 列表为空")
            return []

        results = []
        self.stats['total_pages'] = len(sku_list)

        for i, sku in enumerate(sku_list, 1):
            logger.info(f"进度: {i}/{len(sku_list)} - SKU={sku}")

            result = self.get_price(sku)
            results.append(result)

            # 更新统计
            if result.status == "success":
                self.stats['successful_detections'] += 1
            else:
                self.stats['failed_detections'] += 1

            # 添加延迟（避免被封）
            if i < len(sku_list):
                delay = 2 + (i % 3)  # 2-4 秒随机延迟
                time.sleep(delay)

        return results

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
        return False
