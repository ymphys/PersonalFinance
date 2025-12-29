# PersonalFinance

个人财务数据管理与分析工具，支持支付宝、微信账单的自动合并、清洗、分类与分析。适合希望高效管理个人收支数据、自动化标签分类与可视化分析的用户。

## 主要功能

- 支持支付宝、微信账单导入与合并
- 自动数据清洗与格式统一
- 基于 DeepSeek 的账单分类与标签自动化
- 账单数据可视化与分析（可扩展）
- 支持历史账单增量更新

## 依赖环境

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) 包管理工具
- 主要依赖库见 `pyproject.toml`（如 pandas、notebook、openai 等）

## 安装与使用

### 1. 克隆仓库

```zsh
git clone git@github.com:ymphys/PersonalFinance.git
cd PersonalFinance
```

### 2. 安装依赖

```zsh
uv sync
```

### 3. 获取账单数据

前往支付宝、微信，导出历史账单为 CSV 文件。

创建数据目录并存放账单文件：

```zsh
mkdir -p Data/{Alipay,Wechat,update}
# 将支付宝、微信账单 CSV 文件分别放入对应目录，可用 MMDD.csv 命名区分
```

### 4. 数据更新与清洗流程

#### 合并与清洗

```zsh
uv run update.py
uv run clean.py
```
上述命令会将支付宝、微信账单与历史数据合并，并输出到 `./Data/update/updated.csv` 和 `./Data/update/cleaned.csv`。

#### DeepSeek 自动标签分类

```zsh
uv run label.py
```
`./Data`目录下存在`/update/cleaned.csv`与`cleaned_labeled.csv`，程序会首先合并这两个文件，确保之前已经标注过的数据不再被发送并标注；采用了并发提高速度，默认并发次数为10次；采用了tqdm包显示标注进度；每标注100行数据会写入一次，最终标注完成的数据为`./Data/cleaned_labeled.csv`.

### 5. 数据分析与可视化

`analysis.py` 提供了对已清洗账单（`Data/cleaned_labeled.csv`）的分析与可视化功能，默认会：

1. 汇总收入、支出、净收入，并按类别与子类别统计支出明细。
2. 生成子类别支出饼图（自动移除占比 <2% 的项并合并为「Other」）和低比例子类对比饼图，以及日度支出趋势折线图。
3. 将图表保存在 `Analysis/plots/`，并将分析摘要写入 `Analysis/markdown/analysis.md`（可选指定区间时会生成 `analysis_{start}_{end}.md`）；
4. 解决文件间路径问题，使 Markdown 中的图片链接均为相对路径。

#### 运行方式

```zsh
uv run analysis.py Data/cleaned_labeled.csv
```

可选地加上 `--period START END`（格式如 `2025-01-01 2025-10-30`）只分析该时间段内的流水，脚本会自动筛选、命名输出文件，并打印中文的 Markdown 摘要。

**依赖提示**：脚本需要 `matplotlib`，请保证该依赖已通过 `uv sync` 安装或 `pip install matplotlib`。


## 目录结构说明

```
PersonalFinance/
├── Data/                # 存放账单原始数据与处理结果
│   ├── Alipay/
│   ├── Wechat/
│   └── update/
├── update.py            # 支付宝、微信账单合并脚本
├── clean.py             # 数据清洗脚本
├── label.py             # DeepSeek 分类标签
├── pyproject.toml       # Python 依赖配置
└── README.md
```

## 贡献指南

欢迎提交 issue 和 PR，建议流程：

1. Fork 本仓库
2. 新建分支进行开发
3. 提交 PR 并描述修改内容

## TODO

- 完善数据分析与可视化功能
- 支持微信/支付宝数据定期自动获取
- 优化 GPT 分类准确率与交互体验

## License

MIT
