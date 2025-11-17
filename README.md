# PersonalFinance

个人财务数据管理与分析工具，支持支付宝、微信账单的自动合并、清洗、分类与分析。适合希望高效管理个人收支数据、自动化标签分类与可视化分析的用户。

## 主要功能

- 支持支付宝、微信账单导入与合并
- 自动数据清洗与格式统一
- 基于 GPT 的账单分类与标签自动化
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
uv run alipy_wechat_update.py
uv run clean.py
```
上述命令会将支付宝、微信账单与历史数据合并，并输出到 `./Data/update/alipay_wechat_uptodate.csv` 和 `./Data/update/cleaned.csv`。

#### GPT 自动标签分类

1. 打开 `GPT_labeling.ipynb` Jupyter Notebook
2. 依次运行所有单元格
3. `clean.csv` 与 `cleaned_labeled.csv` 会合并，已标注的 `new_category` 会自动赋值，新增数据将自动调用 GPT 进行分类
4. 最终结果输出到 `cleaned_labeled.csv`

## 目录结构说明

```
PersonalFinance/
├── Data/                # 存放账单原始数据与处理结果
│   ├── Alipay/
│   ├── Wechat/
│   └── update/
├── alipy_wechat_update.py   # 支付宝、微信账单合并脚本
├── clean.py                # 数据清洗脚本
├── GPT_labeling.ipynb      # GPT 分类标签 Jupyter Notebook
├── pyproject.toml          # Python 依赖配置
└── README.md
```

## 贡献指南

欢迎提交 issue 和 PR，建议流程：

1. Fork 本仓库
2. 新建分支进行开发
3. 提交 PR 并描述修改内容

## TODO

- 增加更多数据分析与可视化功能
- 支持更多账单来源
- 优化 GPT 分类准确率与交互体验

## License

MIT