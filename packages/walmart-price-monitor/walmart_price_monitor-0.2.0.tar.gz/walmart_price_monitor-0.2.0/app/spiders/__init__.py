#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫模块
提供 Walmart 平台的价格监控爬虫
"""

from .base_spider import BaseSpider, TabWorker, set_thread_page, clear_thread_page
from .walmart_spider import WalmartPriceSpider
from .walmart_bot_handler import WalmartBotHandler, BotDetectionType

__all__ = [
    'BaseSpider',
    'TabWorker',
    'set_thread_page',
    'clear_thread_page',
    'WalmartPriceSpider',
    'WalmartBotHandler',
    'BotDetectionType'
]
