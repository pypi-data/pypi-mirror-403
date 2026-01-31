#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价格记录器
将价格结果写入钉钉表格
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Optional

from app.models.price_result import PriceResult
from app.dingtalk_doc_reader import DingTalkDocReader

# 钉钉SDK导入
try:
    from alibabacloud_dingtalk.doc_1_0.client import Client as dingtalkdoc_1_0Client
    from alibabacloud_dingtalk.doc_1_0 import models as dingtalkdoc_1_0_models
    from alibabacloud_tea_openapi import models as open_api_models
    from alibabacloud_tea_util import models as util_models
    DINGTALK_SDK_AVAILABLE = True
except ImportError:
    DINGTALK_SDK_AVAILABLE = False

logger = logging.getLogger(__name__)


class PriceRecorder:
    """价格记录器

    将价格结果写入钉钉表格。

    表格结构：
        - 第1行: 日期（"1日"、"2日"...）
        - 第2行: 标题（"商品ID"、"WM链接"、"SKU"、"Price"、"Promo Price"...）
        - 第3行开始: 商品数据
        - A列: 商品ID
        - B列: WM链接
        - C列: SKU
        - D/E列: Price/Promo Price（第一次采集）
        - F/G列: Price/Promo Price（第二次采集）
        - ... 以此类推

    写入逻辑：
        - 从D列开始，每次检查2列（Price + Promo Price）
        - 找到第一个空列（第3行数据为空）
        - 第1行写入日期（如"1日"）
        - 第2行写入标题（"Price"、"Promo Price"）
        - 第3行开始写入价格数据
    """

    DEFAULT_SHEET_NAME = 'ALL'

    def __init__(self, doc_reader: DingTalkDocReader = None):
        """初始化价格记录器

        Args:
            doc_reader: 钉钉文档读取器实例
        """
        self.doc_reader = doc_reader or DingTalkDocReader()
        self.sheet_name = os.getenv('DATA_SHEET_NAME', self.DEFAULT_SHEET_NAME)

        # 初始化钉钉文档客户端
        self._doc_client = None
        if DINGTALK_SDK_AVAILABLE:
            self._doc_client = self._create_doc_client()

        # 本地备份目录
        self.backup_dir = 'data/price_records'
        os.makedirs(self.backup_dir, exist_ok=True)

    def _create_doc_client(self) -> Optional['dingtalkdoc_1_0Client']:
        """创建钉钉文档客户端"""
        if not DINGTALK_SDK_AVAILABLE:
            return None

        try:
            config = open_api_models.Config()
            config.protocol = 'https'
            config.region_id = 'central'
            return dingtalkdoc_1_0Client(config)
        except Exception as e:
            logger.error(f"创建钉钉文档客户端失败: {e}")
            return None

    def record_prices(self, results: List[PriceResult], sheet_name: str = None) -> bool:
        """记录价格结果到钉钉表格

        Args:
            results: 价格结果列表
            sheet_name: 工作表名称

        Returns:
            bool: 是否成功写入
        """
        if not results:
            logger.warning("没有价格结果需要记录")
            return True

        sheet_name = sheet_name or self.sheet_name

        # 尝试写入钉钉表格
        success = self._write_to_dingtalk(results, sheet_name)

        # 无论是否成功，都保存本地备份
        self._save_local_backup(results)

        return success

    def _write_to_dingtalk(self, results: List[PriceResult], sheet_name: str) -> bool:
        """写入钉钉表格

        Args:
            results: 价格结果列表
            sheet_name: 工作表名称

        Returns:
            bool: 是否成功
        """
        if not self.doc_reader.is_enabled():
            logger.warning("钉钉文档功能未启用，跳过写入")
            return False

        if not self._doc_client:
            logger.warning("钉钉文档客户端未初始化，跳过写入")
            return False

        try:
            # 获取文档信息
            doc_info = self.doc_reader.extract_doc_info()
            if not doc_info or not doc_info.get('workbook_id'):
                logger.error("无法获取文档信息")
                return False

            workbook_id = doc_info['workbook_id']

            # 查找工作表
            sheet_id = self.doc_reader._find_sheet_by_name(workbook_id, sheet_name)
            if not sheet_id:
                logger.error(f"未找到工作表: {sheet_name}")
                return False

            # ✅ 修复：智能查找空列并写入（包含日期、标题、数据）
            success = self._update_prices_to_empty_columns(workbook_id, sheet_id, results)

            if success:
                logger.info(f"成功写入 {len(results)} 条价格记录")
            else:
                logger.error("写入价格失败")

            return success

        except Exception as e:
            logger.error(f"写入钉钉表格失败: {e}")
            return False

    def _find_today_column_or_empty(self, workbook_id: str, sheet_id: str) -> Optional[int]:
        """查找今天的列组或第一个空列组

        逻辑：
        1. 读取第1行的所有日期
        2. 如果找到今天的日期（如"30日"），返回那个列组（覆盖模式）
        3. 如果没有找到今天的日期，返回第一个空列组（追加模式）

        Args:
            workbook_id: 工作簿ID
            sheet_id: 工作表ID

        Returns:
            Optional[int]: 列组的起始列号（1-based），如 4=D列, 6=F列
        """
        try:
            # 1. 读取第1行数据（日期行）
            date_row = self.doc_reader._read_sheet_range_single(
                workbook_id, sheet_id, "D1:ZZ1"
            )

            # 生成今天的日期字符串（如"30日"）
            today = datetime.now()
            today_str = f"{today.day}日"

            # 2. 检查是否已经有今天的日期
            if date_row and date_row[0]:
                for col_offset in range(0, len(date_row[0]), 2):
                    cell_value = date_row[0][col_offset] if col_offset < len(date_row[0]) else None
                    if cell_value and str(cell_value).strip() == today_str:
                        col_num = 4 + col_offset  # D列是第4列
                        col_letter = self._col_num_to_letter(col_num)
                        logger.info(f"找到今天的日期 '{today_str}' 在 {col_letter} 列，将覆盖数据")
                        return col_num

            # 3. 没有找到今天的日期，查找第一个空列组
            data = self.doc_reader._read_sheet_range_single(
                workbook_id, sheet_id, "D3:ZZ3"
            )

            if not data or not data[0]:
                logger.info("D列开始为空，使用D/E列（新建）")
                return 4  # D列（从D列开始，第4列）

            row = data[0]

            # 从D列开始，每次检查2列（col_offset=0 对应D列）
            for col_offset in range(0, len(row), 2):
                # 检查当前列组的第一列是否为空
                if col_offset >= len(row) or not row[col_offset] or str(row[col_offset]).strip() == '':
                    col_num = 4 + col_offset  # D列是第4列
                    col_letter = self._col_num_to_letter(col_num)
                    logger.info(f"找到空列组: {col_letter}/{self._col_num_to_letter(col_num+1)}（新建）")
                    return col_num

            # 如果所有列都有数据，返回下一个新列组
            next_col = 4 + len(row) + (len(row) % 2)  # 确保是偶数列（对齐2列一组）
            logger.info(f"所有列都有数据，使用新列组: {self._col_num_to_letter(next_col)}（新建）")
            return next_col

        except Exception as e:
            logger.warning(f"查找列失败: {e}，默认使用D列")
            return 4  # 默认从D列开始

    def _update_prices_to_empty_columns(self, workbook_id: str, sheet_id: str, results: List[PriceResult]) -> bool:
        """将价格写入第一个空列组

        写入结构：
        - 第1行: 日期（如"1日"）
        - 第2行: 标题（"Price"、"Promo Price"）
        - 第3行开始: 价格数据

        Args:
            workbook_id: 工作簿ID
            sheet_id: 工作表ID
            results: 价格结果列表

        Returns:
            bool: 是否成功
        """
        try:
            access_token = self.doc_reader._get_access_token()
            if not access_token:
                logger.error("无法获取访问令牌")
                return False

            # 1. 查找今天的列组或第一个空列组
            start_col = self._find_today_column_or_empty(workbook_id, sheet_id)
            if not start_col:
                logger.error("无法确定写入列位置")
                return False

            col1_letter = self._col_num_to_letter(start_col)
            col2_letter = self._col_num_to_letter(start_col + 1)

            # 2. 生成日期和标题
            today = datetime.now()
            date_str = f"{today.day}日"  # 简化格式：只显示日期
            title_price = "Price"
            title_promo = "Promo Price"

            # 3. 准备数据
            # 第1行: 日期
            # 第2行: 标题
            # 第3行开始: 价格数据
            values = [
                [date_str, ""],                           # 第1行: 日期（只在第一列显示）
                [title_price, title_promo]               # 第2行: 标题
            ]

            # 添加价格数据（从第3行开始）
            for result in results:
                values.append([
                    result.display_price,      # Price列
                    result.display_promo_price  # Promo Price列
                ])

            # 4. 计算写入范围
            end_row = len(results) + 2  # +2 因为前两行是日期和标题
            range_address = f"{col1_letter}1:{col2_letter}{end_row}"

            logger.info(f"写入范围: {range_address}")
            logger.debug(f"数据行数: {len(results)}, 总行数: {end_row}")

            # 5. 构建请求
            headers = dingtalkdoc_1_0_models.UpdateRangeHeaders()
            headers.x_acs_dingtalk_access_token = access_token

            request = dingtalkdoc_1_0_models.UpdateRangeRequest(
                operator_id=self.doc_reader.operator_id,
                values=values
            )

            # 6. 发送请求
            response = self._doc_client.update_range_with_options(
                workbook_id, sheet_id, range_address,
                request, headers, util_models.RuntimeOptions()
            )

            if response and response.body:
                logger.info(f"价格写入成功: {col1_letter}/{col2_letter}列")

                # 7. ✅ 合并日期单元格（D1:E1）
                merge_success = self._merge_date_cells(
                    workbook_id, sheet_id,
                    col1_letter, col2_letter
                )
                if merge_success:
                    logger.info(f"日期单元格合并成功: {col1_letter}1:{col2_letter}1")
                else:
                    logger.warning(f"日期单元格合并失败，请手动合并 {col1_letter}1:{col2_letter}1")

                return True

            return False

        except Exception as e:
            logger.error(f"写入价格失败: {e}")
            if hasattr(e, 'data') and e.data:
                logger.error(f"错误详情: {e.data}")
            return False


    def _merge_date_cells(self, workbook_id: str, sheet_id: str,
                          col1_letter: str, col2_letter: str) -> bool:
        """合并日期单元格（横向合并两列）

        将日期单元格（如 D1:E1）合并为一个单元格

        注意：钉钉文档 API 可能不支持直接合并单元格。
        如果 API 不支持，需要在钉钉表格中手动设置单元格合并。

        Args:
            workbook_id: 工作簿ID
            sheet_id: 工作表ID
            col1_letter: 第一列字母（如 'D'）
            col2_letter: 第二列字母（如 'E'）

        Returns:
            bool: 是否成功合并
        """
        try:
            # ⚠️ 钉钉文档 API 1.0 可能不支持合并单元格
            # 这里尝试使用可能的 API，如果失败则返回 False

            # 方案1：尝试使用 batch_update（如果存在）
            # 方案2：使用特殊的单元格格式
            # 方案3：返回 False，提示手动合并

            # 当前钉钉文档 SDK 没有明确的合并单元格 API
            # 返回 False，在日志中提示需要手动合并
            logger.debug(
                f"钉钉文档 API 暂不支持自动合并单元格。"
                f"请在钉钉表格中手动合并单元格 {col1_letter}1:{col2_letter}1"
            )
            return False

        except Exception as e:
            logger.debug(f"合并单元格失败: {e}")
            return False

    def _col_num_to_letter(self, col: int) -> str:
        """将列号转换为字母

        Args:
            col: 列号（1-based）

        Returns:
            str: 列字母 (A, B, ..., Z, AA, AB, ...)
        """
        result = ""
        while col > 0:
            col, remainder = divmod(col - 1, 26)
            result = chr(65 + remainder) + result
        return result

    def _save_local_backup(self, results: List[PriceResult]):
        """保存本地备份

        Args:
            results: 价格结果列表
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"{self.backup_dir}/prices_{timestamp}.json"

            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'record_count': len(results),
                'records': [r.to_dict() for r in results]
            }

            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)

            logger.debug(f"本地备份已保存: {backup_file}")

        except Exception as e:
            logger.warning(f"保存本地备份失败: {e}")


# 创建全局实例
price_recorder = PriceRecorder()
