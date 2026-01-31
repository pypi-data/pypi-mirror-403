#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SKU 读取器
从钉钉表格读取商品 SKU 列表
"""

import os
import re
import logging
from typing import List, Optional

from app.dingtalk_doc_reader import DingTalkDocReader

logger = logging.getLogger(__name__)


class SKUReader:
    """商品ID读取器

    从钉钉表格的 A 列读取商品ID列表。

    表格结构：
        - 第1行: 日期行（采集日期）
        - 第2行: 标题行（"商品ID"、"WM链接"、"SKU"、"Price"、"Promo Price"）
        - 第3行开始: 商品数据行
        - A列: 商品ID（从第3行开始）
        - B列: WM链接（公式生成）
        - C列: SKU
    """

    # 默认 Sheet 名称
    DEFAULT_SHEET_NAME = 'ALL'

    def __init__(self, doc_reader: DingTalkDocReader = None):
        """初始化 SKU 读取器

        Args:
            doc_reader: 钉钉文档读取器实例
        """
        self.doc_reader = doc_reader or DingTalkDocReader()
        self.sheet_name = os.getenv('DATA_SHEET_NAME', self.DEFAULT_SHEET_NAME)

    def read_skus(self, sheet_name: str = None) -> List[str]:
        """读取商品ID列表（从A列读取）

        注意：方法名为 read_skus 但实际返回的是商品ID列表（10-13位长数字）

        Args:
            sheet_name: 工作表名称，默认使用环境变量配置

        Returns:
            List[str]: 有效的商品ID列表
        """
        sheet_name = sheet_name or self.sheet_name

        if not self.doc_reader.is_enabled():
            logger.warning("钉钉文档功能未启用")
            return []

        try:
            # 解析文档信息
            doc_info = self.doc_reader.extract_doc_info()
            if not doc_info or not doc_info.get('workbook_id'):
                logger.error("无法获取文档信息")
                return []

            workbook_id = doc_info['workbook_id']

            # 查找工作表
            sheet_id = self.doc_reader._find_sheet_by_name(workbook_id, sheet_name)
            if not sheet_id:
                logger.error(f"未找到工作表: {sheet_name}")
                return []

            logger.info(f"读取工作表: {sheet_name}")

            # 读取 A 列数据（商品ID列）
            # ✅ 修复：从第3行开始读取（第1行是日期，第2行是标题）
            data = self.doc_reader._read_sheet_range_single(
                workbook_id, sheet_id, "A3:A1000"
            )

            if not data:
                logger.warning("A 列数据为空")
                return []

            # 提取并验证商品ID
            product_ids = []
            empty_row_count = 0
            invalid_count = 0

            # ✅ 修复：行号从3开始（对应实际表格行号）
            for row_idx, row in enumerate(data, start=3):
                # ✅ 改进空行检测：检查 row 是否为空列表，或第一列是否为空
                if not row or not row[0] or str(row[0]).strip() == '':
                    empty_row_count += 1
                    continue

                product_id = str(row[0]).strip()

                if self._is_valid_product_id(product_id):
                    product_ids.append(product_id)
                else:
                    invalid_count += 1
                    logger.debug(f"跳过无效商品ID (行 {row_idx}): {product_id}")

            logger.info(
                f"读取完成: 有效商品ID={len(product_ids)}, "
                f"空行={empty_row_count}, 无效ID={invalid_count}"
            )
            return product_ids

        except Exception as e:
            logger.error(f"读取 SKU 列表失败: {e}")
            return []

    def _is_valid_product_id(self, product_id: str) -> bool:
        """验证商品ID是否有效

        Walmart 商品ID 是纯数字，长度通常为 8-13 位
        放宽限制以适应不同长度的商品ID

        Args:
            product_id: 待验证的商品ID

        Returns:
            bool: 是否有效
        """
        if not product_id:
            return False

        # 移除可能的前后空白
        product_id = product_id.strip()

        # 检查是否为纯数字
        if not product_id.isdigit():
            logger.debug(f"商品ID非纯数字: {product_id}")
            return False

        # ✅ 关键修复：放宽长度限制（支持 6-15 位）
        # 实际测试发现商品ID长度不固定
        if len(product_id) < 6 or len(product_id) > 15:
            logger.debug(f"商品ID长度异常: {len(product_id)} 位 - {product_id}")
            return False

        return True

    def get_sku_count(self, sheet_name: str = None) -> int:
        """获取商品ID数量（不读取全部数据）

        Args:
            sheet_name: 工作表名称

        Returns:
            int: 商品ID数量
        """
        skus = self.read_skus(sheet_name)
        return len(skus)


# 创建全局实例
sku_reader = SKUReader()
