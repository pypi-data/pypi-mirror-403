# 沃尔玛价格监控工具

每天定时执行，从钉钉表格读取商品SKU，爬取沃尔玛价格并写回表格。

## 功能特性

- 定时任务自动执行（支持 Cron 表达式）
- 从钉钉表格读取商品 SKU
- 自动识别促销价/原价
- 价格数据写回钉钉表格
- 历史价格记录追加
- 钉钉机器人通知

## 快速开始

### 1. 安装

```bash
# 使用 uvx 一键运行（推荐）
uvx walmart-price-monitor

# 或使用 pip 安装
pip install walmart-price-monitor

# 或克隆项目手动安装
git clone <repo-url>
cd WalmartAbby
pip install -e .
```

### 2. 配置

复制 `.env-example` 为 `.env`，填入配置：

```bash
cp .env-example .env
# 编辑 .env 文件
```

主要配置项：

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `CRON_EXPRESSION` | 定时任务表达式 | `0 8 * * *`（每天8点） |
| `DINGTALK_DOC_URL` | 钉钉表格链接 | `https://alidocs.dingtalk.com/i/nodes/xxx` |
| `DATA_SHEET_NAME` | SKU 所在工作表名 | `ALL` |

### 3. 运行

```bash
# 定时任务模式（默认）
python run.py

# 单次执行模式
python run.py --once

# uvx 一键运行
uvx walmart-monitor
uvx wm --once  # 简写
```

## 钉钉表格结构

| 列 | 内容 | 说明 |
|----|------|------|
| A | 序号 | 可选 |
| B | 商品名称 | 可选 |
| C | SKU | **必填**，沃尔玛商品ID |
| D | 当前价格 | 程序写入 |
| E | 促销价 | 程序写入（有促销时） |
| F+ | 历史价格 | 程序自动追加 |

- 第1行为标题行
- 数据从第2行开始
- SKU 为纯数字格式（如 `10101089`）

## 价格识别逻辑

1. 有促销时（存在划线价）：
   - D列：原价（划线价）
   - E列：促销价（当前显示价）

2. 无促销时：
   - D列：当前价格
   - E列：空

## 通知示例

```
### 沃尔玛价格监控报告

**执行时间**: 2024-02-01 08:00:00 ~ 08:15:32

**扫描统计**:
- 商品总数: 150 个
- 获取成功: 145 个
- 有促销价: 23 个
- 获取异常: 5 个

**异常商品**:
1. SKU: 10101089 - 页面不存在
2. SKU: 10102007 - 商品不可用

---

数据已更新至钉钉表格
```

## 目录结构

```
walmart-monitor/
├── app/
│   ├── cli.py              # 入口（定时任务）
│   ├── config.py           # 配置管理
│   ├── notifier.py         # 钉钉通知
│   ├── dingtalk_doc_reader.py  # 钉钉文档API
│   ├── models/
│   │   └── price_result.py # 价格结果模型
│   ├── readers/
│   │   └── sku_reader.py   # SKU读取器
│   ├── recorders/
│   │   └── price_recorder.py # 价格记录器
│   ├── selectors/
│   │   └── walmart_selectors.py # 页面选择器
│   └── spiders/
│       ├── base_spider.py     # 爬虫基类
│       └── walmart_spider.py  # 价格爬虫
├── run.py                  # 启动脚本
├── .env-example            # 配置示例
└── pyproject.toml          # 项目配置
```

## License

MIT
