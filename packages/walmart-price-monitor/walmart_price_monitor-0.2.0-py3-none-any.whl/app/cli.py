#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
沃尔玛价格监控 - 统一启动入口

运行模式：
- 默认: 定时任务模式（使用 CRON_EXPRESSION 配置）
- --once: 单次执行模式
"""

import os
import sys
import time
import signal
import logging
from datetime import datetime
from pathlib import Path
from typing import List

from dotenv import load_dotenv


def load_env_config():
    """
    加载环境变量配置
    优先级：当前工作目录 .env > 用户主目录 .walmart-monitor/.env > 系统环境变量
    """
    # 1. 当前工作目录
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        load_dotenv(cwd_env, override=True)
        print(f"[配置] 已加载: {cwd_env}")
        return

    # 2. 用户主目录下的配置目录
    home_env = Path.home() / ".walmart-monitor" / ".env"
    if home_env.exists():
        load_dotenv(home_env, override=True)
        print(f"[配置] 已加载: {home_env}")
        return

    # 3. 没有找到 .env 文件，使用系统环境变量
    print("[配置] 未找到 .env 文件，使用系统环境变量")
    print(f"[提示] 可在以下位置创建 .env 文件:")
    print(f"       - {cwd_env}")
    print(f"       - {home_env}")


# 加载环境变量
load_env_config()

# 配置项
CRON_EXPRESSION = os.getenv("CRON_EXPRESSION", "0 8 * * *")  # 默认每天8点执行


def setup_logging():
    """配置日志"""
    log_dir = "data"
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'app.log'), encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def run_price_monitor_task():
    """执行价格监控任务"""
    logger = logging.getLogger(__name__)

    from app.readers import SKUReader
    from app.recorders import PriceRecorder
    from app.spiders import WalmartPriceSpider
    from app.notifier import ding_talk_notifier
    from app.config import settings
    from app.models import PriceResult

    start_time = datetime.now()
    logger.info("=" * 50)
    logger.info(f"价格监控任务开始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)

    try:
        # 1. 读取 SKU 列表
        reader = SKUReader()
        skus = reader.read_skus()

        if not skus:
            logger.warning("没有找到 SKU，任务结束")
            return

        logger.info(f"读取到 {len(skus)} 个 SKU")

        # 发送开始通知
        title = "沃尔玛价格监控启动"
        text = f"""### 沃尔玛价格监控启动

**启动时间**: {start_time.strftime('%Y-%m-%d %H:%M:%S')}

**商品数量**: {len(skus)} 个

---

正在获取商品价格..."""
        ding_talk_notifier.send_markdown(title, text, is_at_all=False)

        # 2. 执行价格爬取
        user_data_path = settings.CHROME_USER_DATA_PATH or None

        with WalmartPriceSpider(user_data_path=user_data_path) as spider:
            results: List[PriceResult] = spider.run(skus, data_source="dingtalk")

        # 3. 记录结果到钉钉表格
        recorder = PriceRecorder()
        recorder.record_prices(results)

        # 4. 发送汇总通知
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # 统计
        success_count = sum(1 for r in results if r.status == "success")
        error_count = sum(1 for r in results if r.status != "success")
        promo_count = sum(1 for r in results if r.is_on_promotion)

        # 收集异常商品
        error_items = [r for r in results if r.status != "success"]
        error_list_text = ""
        if error_items:
            error_list_text = "\n\n**异常商品**:\n"
            for i, item in enumerate(error_items[:10], 1):  # 最多显示10个
                error_list_text += f"{i}. SKU: {item.sku} - {item.error_message}\n"
            if len(error_items) > 10:
                error_list_text += f"...(还有 {len(error_items) - 10} 个)"

        title = "沃尔玛价格监控完成"
        text = f"""### 沃尔玛价格监控报告

**执行时间**: {start_time.strftime('%Y-%m-%d %H:%M:%S')} ~ {end_time.strftime('%H:%M:%S')}

**耗时**: {duration:.0f} 秒

---

**扫描统计**:
- 商品总数: {len(results)} 个
- 获取成功: {success_count} 个
- 有促销价: {promo_count} 个
- 获取异常: {error_count} 个
{error_list_text}
---

数据已更新至钉钉表格"""

        ding_talk_notifier.send_markdown(title, text, is_at_all=False)

        logger.info("价格监控任务完成")
        logger.info(f"成功: {success_count}, 异常: {error_count}, 促销: {promo_count}")

    except Exception as e:
        logger.error(f"价格监控任务失败: {e}", exc_info=True)

        # 发送错误通知
        title = "沃尔玛价格监控失败"
        text = f"""### 沃尔玛价格监控失败

**错误信息**: {str(e)}

**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

请检查日志获取详细信息。"""

        try:
            ding_talk_notifier.send_markdown(title, text, is_at_all=True)
        except Exception:
            pass


def run_scheduler():
    """启动定时任务调度器"""
    try:
        from croniter import croniter
    except ImportError:
        print("错误: 请先安装 croniter 库: pip install croniter")
        sys.exit(1)

    logger = logging.getLogger(__name__)
    logger.info("启动定时任务调度器")
    logger.info(f"Cron 表达式: {CRON_EXPRESSION}")

    # 信号处理
    running = True

    def signal_handler(signum, frame):
        nonlocal running
        logger.info("收到停止信号，正在退出...")
        running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 计算下次执行时间
    cron = croniter(CRON_EXPRESSION, datetime.now())

    def get_next_run_time():
        return cron.get_next(datetime)

    next_run = get_next_run_time()
    logger.info(f"下次执行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

    while running:
        now = datetime.now()

        if now >= next_run:
            try:
                run_price_monitor_task()
            except Exception as e:
                logger.error(f"定时任务执行失败: {e}", exc_info=True)

            # 计算下次执行时间
            cron = croniter(CRON_EXPRESSION, datetime.now())
            next_run = get_next_run_time()
            logger.info(f"下次执行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

        # 休眠 1 秒
        time.sleep(1)

    logger.info("定时任务调度器已停止")


def main():
    """主入口"""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("沃尔玛价格监控工具 v0.2.0")
    logger.info("=" * 60)

    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # 单次执行模式
        logger.info("运行模式: 单次执行")
        run_price_monitor_task()
    else:
        # 定时任务模式
        logger.info("运行模式: 定时任务")
        run_scheduler()


if __name__ == "__main__":
    main()
