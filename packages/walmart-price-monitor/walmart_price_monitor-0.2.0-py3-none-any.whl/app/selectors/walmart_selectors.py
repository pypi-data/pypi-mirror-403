#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Walmart 页面选择器
统一管理所有 Walmart 页面的 CSS/XPath 选择器

基于需求文档中的 HTML 示例设计
"""


class WalmartSelectors:
    """Walmart 页面选择器"""

    # === 页面状态检测 ===
    class PageStatus:
        """页面状态检测选择器"""
        # 购买区域容器
        BUY_BOX = 'css:[data-testid="flex-container"].buy-box-container'
        BUY_BOX_ALT = '.buy-box-container'

        # 商品标题
        PRODUCT_TITLE = '@data-testid=product-title'
        PRODUCT_TITLE_ALT = 'css:h1[itemprop="name"]'

        # 验证码检测
        CAPTCHA = '@data-testid=captcha'
        CAPTCHA_ALT = '#captcha-container'

        # 搜索框（用于判断页面是否加载完成）
        SEARCH_BOX = '@data-testid=search-box'
        SEARCH_BOX_ALT = '#global-search-input'

        # 404 页面检测
        NOT_FOUND = 'text=This page could not be found'
        NOT_FOUND_ALT = 'text=We couldn\'t find that page'

    # === 防爬验证页面 ===
    class BotDetection:
        """防爬/人机验证页面选择器"""
        # 验证页面的 Logo 按钮（需要点击进入下一步）
        HEADER_LOGO = 'a.header-logo'
        HEADER_LOGO_ALT = 'a[aria-label*="Walmart"]'

        # Logo 内的 spark 图标
        SPARK_ICON = 'span.elc-icon-spark'
        SPARK_ICON_ALT = 'span.spark'

        # 所有验证页面选择器
        ALL_LOGO_BUTTONS = [
            'a.header-logo',
            'a[aria-label*="Walmart"][href="/"]',
            'a[aria-label*="Save Money"]'
        ]

    # === 库存状态 ===
    class Stock:
        """库存状态选择器"""
        # 不可用状态
        NOT_AVAILABLE = 'text=Not Available'
        NOT_AVAILABLE_DIV = '.dark-gray.lh-copy:contains("Not Available")'

        # 缺货状态
        OUT_OF_STOCK = '@data-testid=out-of-stock-message'
        OUT_OF_STOCK_TEXT = 'text=Out of stock'

        # 售罄状态
        SOLD_OUT = 'text=Sold out'

        # 暂时不可用
        TEMPORARILY_UNAVAILABLE = 'text=Temporarily unavailable'

        # 所有异常状态选择器
        ALL_UNAVAILABLE = [
            'text=Not Available',
            'text=Out of stock',
            'text=Sold out',
            'text=Temporarily unavailable',
            '@data-testid=out-of-stock-message'
        ]

    # === 购物车按钮 ===
    class CartButton:
        """购物车按钮选择器"""
        # 主要的 Add to Cart 按钮
        ATC_BUTTON = '@data-automation-id=atc'

        # ATC 容器
        ATC_CONTAINER = '@data-testid=atc-buynow-container'

        # 备选选择器
        ATC_BUTTON_ALT = 'css:button[data-dca-name="ItemBuyBoxAddToCartButton"]'
        ATC_TEXT = 'text=Add to cart'

        # 所有 ATC 选择器（按优先级排序）
        ALL = [
            '@data-automation-id=atc',
            'css:button[data-dca-name="ItemBuyBoxAddToCartButton"]',
            'css:[data-testid="atc-buynow-container"] button',
            'text=Add to cart'
        ]

    # === 价格信息 ===
    class Price:
        """价格选择器 - 用于提取商品价格

        基于需求文档中的 HTML 示例:
        - 当前/促销价: <span itemprop="price" data-seo-id="hero-price">$224.63</span>
        - 划线原价: <span data-seo-id="strike-through-price" class="strike">$299.99</span>
        - 促销标识: "Now" 前缀或 "You save" 区域
        """

        # === 当前价格/促销价 (hero-price) ===
        # 有促销时显示 "Now $999.99"，无促销时显示 "$34.99"
        CURRENT_PRICE = 'css:span[itemprop="price"][data-seo-id="hero-price"]'
        CURRENT_PRICE_ALT = '@data-seo-id=hero-price'

        # === 划线原价 (strike-through-price) - 仅促销时存在 ===
        STRIKE_THROUGH_PRICE = '@data-seo-id=strike-through-price'
        STRIKE_THROUGH_ALT = 'css:span.strike[data-seo-id="strike-through-price"]'
        STRIKE_THROUGH_CLASS = 'css:span.strike'

        # === 促销标识 ===
        # "You save" 区域
        YOU_SAVE_INDICATOR = 'css:[data-testid="dollar-saving"]'
        YOU_SAVE_TEXT = 'text=You save'

        # "Was" 价格区域（部分页面使用）
        WAS_PRICE = 'css:[data-testid="was-price"]'
        WAS_PRICE_TEXT = 'text=Was'

        # 价格容器
        PRICE_WRAP = '@data-testid=price-wrap'

        # === 选择器列表 ===
        # 当前价格选择器（按优先级排序）
        ALL_CURRENT_PRICE = [
            'css:span[itemprop="price"][data-seo-id="hero-price"]',  # 最精确
            '@data-seo-id=hero-price',                               # DrissionPage原生
            '@itemprop=price',                                       # 语义化
            'css:[data-testid="price-wrap"] span[itemprop="price"]',
        ]

        # 原价选择器（划线价）
        ALL_ORIGINAL_PRICE = [
            '@data-seo-id=strike-through-price',
            'css:span.strike[data-seo-id="strike-through-price"]',
            # 移除 'css:span.strike' - 太宽泛，会匹配非价格元素
            'css:[data-testid="was-price"] span',
        ]

        # 兼容旧代码
        ALL = ALL_CURRENT_PRICE

    # === 卖家信息 ===
    class Seller:
        """卖家信息选择器"""
        SELLER_NAME = '@data-testid=seller-name'
        SOLD_BY = 'text=Sold by'
        SHIPPED_BY = 'text=Shipped by'

        # Walmart 官方卖家标识
        OFFICIAL_SELLERS = ['walmart', 'walmart.com', 'walmart seller']

    # === 配送信息 ===
    class Delivery:
        """配送信息选择器"""
        DELIVERY_DATE = '@data-testid=delivery-date'
        PICKUP_AVAILABLE = '@data-testid=pickup-available'
        SHIPPING_INFO = '@data-testid=shipping-info'


class WalmartTimeouts:
    """Walmart 超时配置"""
    QUICK = 0.5
    SHORT = 1
    NORMAL = 2
    MEDIUM = 3
    LONG = 5
    PAGE_LOAD = 10
    MODAL_WAIT = 8
