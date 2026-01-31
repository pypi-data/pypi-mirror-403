#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置模块
管理所有环境变量配置
"""

import os
import random
import logging
from typing import List, Optional
from dotenv import load_dotenv

# 只在模块加载时调用一次
load_dotenv()


def setup_logging(log_file: str = "data/app.log") -> None:
    """
    统一配置日志系统。

    Args:
        log_file: 日志文件路径
    """
    # 确保日志目录存在
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


# 模块级 logger
logger = logging.getLogger(__name__)


class Settings:
    """加载所有环境变量配置"""

    # === 钉钉通知配置 ===
    DINGTALK_WEBHOOK: str = os.getenv("DINGTALK_WEBHOOK", "")
    DINGTALK_SECRET: str = os.getenv("DINGTALK_SECRET", "")
    # 钉钉 @ 指定人员手机号（多个用逗号分隔，为空则 @所有人）
    DINGTALK_AT_MOBILES: str = os.getenv("DINGTALK_AT_MOBILES", "")

    # === Chrome 配置 ===
    CHROME_USER_DATA_PATH: str = os.getenv("CHROME_USER_DATA_PATH", "")

    # === 定时任务配置 ===
    # 默认每天8点执行
    CRON_EXPRESSION: str = os.getenv("CRON_EXPRESSION", "0 8 * * *")

    # === 钉钉文档配置 ===
    # 钉钉文档功能开关
    DINGTALK_DOC_ENABLED: bool = os.getenv(
        "DINGTALK_DOC_ENABLED", "false").lower() in ("true", "1")

    # 钉钉文档 URL
    DINGTALK_DOC_URL: str = os.getenv("DINGTALK_DOC_URL", "")

    # 钉钉应用凭证
    DINGTALK_APP_KEY: str = os.getenv("DINGTALK_APP_KEY", "")
    DINGTALK_APP_SECRET: str = os.getenv("DINGTALK_APP_SECRET", "")
    DINGTALK_OPERATOR_ID: str = os.getenv("DINGTALK_OPERATOR_ID", "")

    # 数据源 Sheet 名称
    DATA_SHEET_NAME: str = os.getenv("DATA_SHEET_NAME", "ALL")


class ProxyConfig:
    """代理配置"""
    enabled: bool = os.getenv('PROXY_ENABLED', 'false').lower() in ('true', '1')
    pool: List[str] = []

    def __init__(self):
        proxy_pool_str = os.getenv('PROXY_POOL', '')
        if self.enabled and proxy_pool_str:
            self.pool = [proxy.strip() for proxy in proxy_pool_str.split(',') if proxy.strip()]


def get_random_proxy() -> Optional[str]:
    """
    从代理池中随机选择一个代理。
    """
    config = ProxyConfig()
    if config.enabled and config.pool:
        return random.choice(config.pool)
    return None


# 全局配置实例
settings = Settings()


if __name__ == '__main__':
    # 用于测试配置加载
    setup_logging()
    logger.info("配置加载测试")
    logger.info(f"钉钉文档启用: {settings.DINGTALK_DOC_ENABLED}")
    logger.info(f"Cron 表达式: {settings.CRON_EXPRESSION}")
