#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
沃尔玛价格监控工具 - 启动入口

使用方式：
    python run.py           # 定时任务模式（默认）
    python run.py --once    # 单次执行模式
"""

from app.cli import main

if __name__ == "__main__":
    main()
