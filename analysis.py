import argparse
from pathlib import Path
from typing import Sequence
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib
# 设置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'Microsoft YaHei', 'PingFang SC', 'STHeiti']  # 优先使用这些字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

def load_transactions(file_path: Path) -> pd.DataFrame:
    """Load the raw CSV transactions into a DataFrame."""
    return pd.read_csv(file_path)


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize datetime, amount, and flow descriptors."""
    cleaned = df.copy()
    cleaned["datetime"] = pd.to_datetime(
        cleaned["Date"].fillna("") + " " + cleaned["Time"].fillna(""),
        errors="coerce",
    )
    cleaned["Amount"] = pd.to_numeric(cleaned["Amount"], errors="coerce").fillna(0.0)
    flow_map = {1: "expense", 0: "transfer", -1: "income"}
    cleaned["flow"] = cleaned["in/out"].map(flow_map).fillna("unknown")
    cleaned["Category"] = cleaned["Category"].fillna("uncategorized").astype(str).str.strip()
    cleaned["sub_category"] = (
        cleaned["sub_category"].fillna("uncategorized").astype(str).str.strip()
    )
    return cleaned


def parse_period(period: Sequence[str] | None) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    """Return normalized start and end timestamps when a period is supplied."""
    if not period:
        return None, None
    start = pd.to_datetime(period[0], errors="coerce")
    end = pd.to_datetime(period[1], errors="coerce")
    if pd.isna(start) or pd.isna(end):
        raise ValueError("Both START and END must be valid dates when using --period.")
    if start > end:
        raise ValueError("Start date must not be later than end date.")
    return start, end


def filter_transactions_by_period(
    df: pd.DataFrame, start: pd.Timestamp | None, end: pd.Timestamp | None
) -> pd.DataFrame:
    if start is None or end is None:
        return df
    mask = (
        df["datetime"].notna()
        & (df["datetime"] >= start)
        & (df["datetime"] <= end)
    )
    return df[mask].copy()


def summarize_cash_flow(df: pd.DataFrame) -> tuple[float, float, float]:
    expenses = df[df["flow"] == "expense"]["Amount"].sum()
    income = df[df["flow"] == "income"]["Amount"].sum()
    return income, expenses, income - expenses


def spending_by_category_sub_category(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    expenses = df[df["flow"] == "expense"]
    by_cat = (
        expenses.groupby("Category", dropna=False)["Amount"]
        .sum()
        .sort_values(ascending=False)
    )
    by_sub = (
        expenses.groupby("sub_category", dropna=False)["Amount"]
        .sum()
        .sort_values(ascending=False)
    )
    return by_cat, by_sub


def daily_spending_summary(df: pd.DataFrame) -> pd.Series:
    expenses = df[df["flow"] == "expense"].copy()
    expenses["date"] = expenses["datetime"].dt.date
    return expenses.groupby("date")["Amount"].sum().sort_index()


def top_expenses(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    expense = df[df["flow"] == "expense"]
    return expense.sort_values("Amount", ascending=False).head(top_n)


def investment_inflows(df: pd.DataFrame) -> tuple[float, pd.Series]:
    investment = df[df["Category"].str.lower() == "investment"]
    total = investment["Amount"].sum()
    by_sub = (
        investment.groupby("sub_category", dropna=False)["Amount"]
        .sum()
        .sort_values(ascending=False)
    )
    return total, by_sub


def plot_expenses_by_subcategory(
    by_sub: pd.Series, output_dir: Path, base_name: str, min_percentage: float = 2.0
) -> tuple[Path | None, pd.Series]:
    positive = by_sub[by_sub > 0]
    total = positive.sum()
    if positive.empty or total == 0:
        return None, positive
    percentages = positive / total * 100
    keep_large = percentages >= min_percentage
    filtered = positive[keep_large].copy()
    others_sum = positive[~keep_large].sum()
    if others_sum > 0:
        filtered["Other (<2%)"] = others_sum
    if filtered.empty:
        return None, positive
    output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(
        filtered,
        labels=filtered.index,
        autopct="%1.1f%%",
        startangle=140,
        textprops={"fontsize": 8},
    )
    ax.set_title("Expenses by Sub-category")
    path = output_dir / f"{base_name}_expenses_by_sub_category.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path, positive


def plot_minor_subcategories(
    by_sub: pd.Series, total: float, output_dir: Path, base_name: str, min_percentage: float = 2.0
) -> Path | None:
    if total == 0:
        return None
    percentages = by_sub / total * 100
    minor = by_sub[percentages < min_percentage]
    if minor.empty:
        return None
    minor_total = minor.sum()
    output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 6))

    def autopct(pct: float) -> str:
        relative = pct * minor_total / total
        return f"{relative:.1f}%"

    ax.pie(
        minor,
        labels=minor.index,
        autopct=autopct,
        startangle=140,
        textprops={"fontsize": 8},
    )
    ax.set_title("Minor Sub-categories (<2% of total spending)")
    path = output_dir / f"{base_name}_minor_subcategory_comparison.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_spending_trend(
    daily: pd.Series, output_dir: Path, base_name: str
) -> Path | None:
    if daily.empty:
        return None
    output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(daily.index, daily.values, marker="o")
    ax.set_title("Daily Expense Trend")
    ax.set_xlabel("Date")
    ax.set_ylabel("Spent (CNY)")
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.autofmt_xdate()
    path = output_dir / f"{base_name}_spending_time_series.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def build_summary_md(
    income: float,
    expenses: float,
    net: float,
    by_cat: pd.Series,
    daily: pd.Series,
    investment_total: float,
    investment_by_sub: pd.Series,
    top_expenses_df: pd.DataFrame,
    cat_plot: Path | None,
    minor_plot: Path | None,
    trend_plot: Path | None,
) -> str:
    lines = ["# 分析摘要", ""]
    lines.append(f"- 总收入：{income:,.2f} CNY")
    lines.append(f"- 总支出：{expenses:,.2f} CNY")
    lines.append(f"- 净收入：{net:,.2f} CNY")
    if not by_cat.empty:
        top_cat = by_cat.index[0]
        lines.append(f"- 最大支出类目：{top_cat}（{by_cat.iloc[0]:,.2f} CNY）")
    if not daily.empty:
        highest_day = daily.idxmax()
        lines.append(f"- 支出最高日：{highest_day}（{daily.max():,.2f} CNY）")
    if investment_total:
        top_invest = investment_by_sub.index[0] if not investment_by_sub.empty else "N/A"
        lines.append(
            f"- 投资收入总额：{investment_total:,.2f} CNY（最大子类：{top_invest}）"
        )

    if cat_plot or minor_plot or trend_plot:
        lines.extend(["", "## 可视化图表", ""])
    if cat_plot:
        lines.append("### 子类支出分布")
        lines.append(
            "饼图展示本次分析中各子类支出所占比例，剔除低于2%的细分类以保持可读性。"
        )
        lines.append("")
        lines.append(f"![按子类分布的支出]({cat_plot.as_posix()})")
        lines.append("")
    if minor_plot:
        lines.append("### 低比例子类对比（<2%）")
        lines.append(
            "饼图突出展示占总支出比例低于2%的子类，百分比表示其相对于整体支出的占比，方便对比。"
        )
        lines.append("")
        lines.append(f"![低比例子类]({minor_plot.as_posix()})")
        lines.append("")
    if trend_plot:
        lines.append("### 日度支出趋势")
        lines.append("折线图展示分析期间每日的累计支出变化。")
        lines.append("")
        lines.append(f"![日度支出趋势]({trend_plot.as_posix()})")
        lines.append("")

    if not top_expenses_df.empty:
        lines.append("## 主要支出明细")
        for i, row in enumerate(top_expenses_df.itertuples(index=False), 1):
            desc = row.Product_Description or "无描述"
            date = (
                row.datetime.date().isoformat()
                if pd.notna(row.datetime)
                else "未知日期"
            )
            lines.append(
                f"{i}. {desc} — {row.Amount:,.2f} CNY，{date}，付款方式："
                f"{row.Payment_Method or '未知'}"
            )

    return "\n".join(lines)


def build_basename(start: pd.Timestamp | None, end: pd.Timestamp | None) -> str:
    if start is None or end is None:
        return "analysis"
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")
    return f"analysis_{start_str}_{end_str}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze personal finance transactions.")
    parser.add_argument(
        "input_file",
        nargs="?",
        type=Path,
        default=Path("Data/cleaned_labeled.csv"),
        help="Path to the cleaned transactions CSV.",
    )
    parser.add_argument(
        "--plots-dir",
        type=Path,
        default=Path("plots"),
        help="Directory to store generated visuals.",
    )
    parser.add_argument(
        "--period",
        nargs=2,
        metavar=("START", "END"),
        help="Optional inclusive date range (YYYY-MM-DD) to limit the analysis.",
    )
    args = parser.parse_args()

    df = load_transactions(args.input_file)
    cleaned = clean_transactions(df)
    start, end = parse_period(args.period)
    scoped = filter_transactions_by_period(cleaned, start, end)

    income, expenses, net = summarize_cash_flow(scoped)
    by_cat, by_sub = spending_by_category_sub_category(scoped)
    daily = daily_spending_summary(scoped)
    top_exp_df = top_expenses(scoped)
    investment_total, investment_by_sub = investment_inflows(scoped)

    base_name = build_basename(start, end)
    cat_plot, positive_sub = plot_expenses_by_subcategory(by_sub, args.plots_dir, base_name)
    positive_total = positive_sub.sum()
    minor_plot = plot_minor_subcategories(positive_sub, positive_total, args.plots_dir, base_name)
    trend_plot = plot_spending_trend(daily, args.plots_dir, base_name)

    summary_text = build_summary_md(
        income,
        expenses,
        net,
        by_cat,
        daily,
        investment_total,
        investment_by_sub,
        top_exp_df,
        cat_plot,
        minor_plot,
        trend_plot,
    )
    print(summary_text)
    summary_path = Path(f"{base_name}.md")
    summary_path.write_text(summary_text, encoding="utf-8")
    print(f"\nSummary written to `{summary_path}`")


if __name__ == "__main__":
    main()
