import pandas as pd
import re
from pathlib import Path

# ================= 配置参数 =================
# MERGE_PATH = 'Data/hand_made/merge.csv'
UPDATE_PATH = 'Data/update/alipay_wechat_uptodate.csv'
OUTPUT_PATH = 'Data/update/cleaned.csv'

# 预编译正则表达式
REGEX_MAP = [
    (re.compile(r'医疗健康'), 'medical'),
    (re.compile(r'家居家装|住房物业'), 'housing'),
    (re.compile(r'数码电器'), 'digital'),
    (re.compile(r'服饰'), 'clothing'),
    (re.compile(r'美容美发'), 'hair_cut'),
    (re.compile(r'爱车'), 'car'),
    (re.compile(r'运动户外'), 'outdoor'),
    (re.compile(r'保险'), 'insurance'),
    (re.compile(r'红包|转账'), 'red_packet'),
    (re.compile(r'商户消费|超市购物|便利店|付款|日用百货|母婴亲子|groceries|服务'), 'shopping'),
    (re.compile(r'退款'), 'refund'),
    (re.compile(r'捐赠'), 'donation'),
    (re.compile(r'零钱|账户存取'), 'inner_transfer'),
    (re.compile(r'信用借还'), 'credit_pay'),
    (re.compile(r'交通出行|transport'), 'transportation'),
    (re.compile(r'餐饮美食'), 'food'),
    (re.compile(r'酒店旅游'), 'travel'),
    (re.compile(r'投资理财'), 'investment'),
    (re.compile(r'充值'), 'recharge'),
    (re.compile(r'其他'), 'other'),
    (re.compile(r'教育培训|school'), 'education'),
    (re.compile(r'文化休闲'), 'entertainment'),
    (re.compile(r'收入|收款'), 'income'),
]


def map_category(cat):
    """根据正则表达式映射类别"""
    if not isinstance(cat, str):
        return cat  # 如果不是字符串（如 NaN），直接返回
    for pattern, value in REGEX_MAP:
        if pattern.search(cat):
            return value
    return cat


# def clean_and_merge(merge_path, update_path, output_path):
def clean_and_merge(update_path, output_path):
    """主处理流程，合并、清洗、重命名、导出"""
    try:
        # df = pd.read_csv(merge_path)
        df = pd.read_csv(update_path)
    except Exception as e:
        print(f"读取文件失败: {e}")
        return

    # 合并数据
    # df = pd.concat([df, df_update], ignore_index=True)
    # cols = list(df_update.columns) + [col for col in df.columns if col not in df_update.columns]
    # df = df[cols]
    df.sort_values(by=['Date', 'Time', 'Amount'], inplace=True)
    try:
        df['Date'] = pd.to_datetime(df['Date'])
        df['in/out'] = pd.to_numeric(df['in/out'], errors='coerce').astype('Int64')
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').astype('Float64')
        df['Category'] = df['Category'].str.lower()
    except Exception as e:
        print(f"数据类型转换失败: {e}")
        return

    # 合并明细
    condition1 = df['Time'].isna() & df.apply(
        lambda row: (
            ((df['Date'] == row['Date']) &
             (df['Amount'] == row['Amount']) &
             df['Time'].notna()).any()
        ) if pd.isna(row['Time']) else False,
        axis=1
    )
    condition2 = df['Time'].notna() & df.apply(
        lambda row: (
            ((df['Date'] == row['Date']) &
             (df['Amount'] == row['Amount']) &
             df['Time'].isna()).any()
        ) if pd.notna(row['Time']) else False,
        axis=1
    )
    mask = condition1 | condition2
    df_pair = df.loc[mask].copy()
    df_nan = df_pair[df_pair['Time'].isna()]
    df_notna = df_pair[df_pair['Time'].notna()]
    df_merged = df_notna.reset_index().merge(
        df_nan[['Date', 'Amount', 'Category', 'Product_Description']],
        on=['Date', 'Amount'],
        suffixes=('', '_from_nan')
    )
    df.loc[df_merged['index'], 'Category'] = df_merged['Category_from_nan'].values
    df.loc[df_merged['index'], 'Note'] = df_merged['Product_Description_from_nan'].values
    df.loc[mask].sort_values(['Date','Amount'],inplace=False,ascending=False)
    df.drop(df[df['Time'].isna()].index, inplace=True)

    # 替换无效字符
    df.replace(['/', 'NaN'], '', inplace=True)
    # 类别重命名
    df['Category'] = df['Category'].apply(map_category)

    try:
        df.to_csv(output_path, index=False)
        print(f"清洗后数据已保存到: {output_path}")
    except Exception as e:
        print(f"保存文件失败: {e}")


if __name__ == "__main__":
    # clean_and_merge(MERGE_PATH, UPDATE_PATH, OUTPUT_PATH)
    clean_and_merge(UPDATE_PATH, OUTPUT_PATH)