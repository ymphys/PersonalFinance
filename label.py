import pandas as pd
import requests
import os
import concurrent.futures
from tqdm import tqdm

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

def deepseek_label(prompt, api_key):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0
    }
    response = requests.post(url, headers=headers, json=data, timeout=30)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content'].strip()

def row_to_prompt(row):
    return (
        f"日期：{row['Date']}，时间：{row['Time']}，类别：{row['Category']}，收支：{row['in/out']}，"
        f"金额：{row['Amount']}，描述：{row['Product_Description']}，状态：{row['Status']}，备注：{row['Note']}，"
        f"对方：{row['Counterparty']}，对方账号：{row['Counterparty_Account']}，支付方式：{row['Payment_Method']}。\n"
        "请为这条流水分配一个详细类别，从以下标签中选择："
        "['购物消费', '餐饮食品', '社交娱乐', '教育学习', '通讯服务', '投资理财', '慈善捐赠', '住房租金', '人情往来', '转账汇款', '保险服务', '医疗健康', '交通出行', '数字服务', '旅行旅游', '个人护理', '家庭生活', '收入', '退款']" \
        "只返回分类结果，每行一个"
    )

# 0. 读取数据
df = pd.read_csv('Data/update/cleaned.csv')
df_labeled = pd.read_csv('Data/update/cleaned_labeling.csv')

# 合并 Date 和 Time 以及 sub_category
df = df.merge(
    df_labeled[['Date', 'Time', 'sub_category']].rename(columns={'sub_category': 'sub_category_labeled'}),
    on=['Date', 'Time'],
    how='left'
)

if 'sub_category' not in df.columns:
    df['sub_category'] = ''

df['sub_category'] = df['sub_category_labeled'].combine_first(df['sub_category'])
df.drop(columns=['sub_category_labeled'], inplace=True)

mask = df['sub_category'] == ''
indices_to_process = df[mask].index.tolist()

def process_row(idx):
    prompt = row_to_prompt(df.loc[idx])
    try:
        label = deepseek_label(prompt, DEEPSEEK_API_KEY)
        return idx, label, None
    except Exception as e:
        return idx, None, e

# 使用线程池并发处理，最大并发数设置为10（可根据API限制调整）
max_workers = 250
with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    futures = {executor.submit(process_row, idx): idx for idx in indices_to_process}

    for i, future in enumerate(tqdm(concurrent.futures.as_completed(futures), total=len(futures))):
        idx = futures[future]
        try:
            result_idx, label, error = future.result()
            if error:
                print(f"Error at {result_idx}: {error}")
            else:
                df.at[result_idx, 'sub_category'] = label
                # 每处理100条数据保存一次进度
                if i % 100 == 0:
                    df.to_csv('Data/cleaned_labeled.csv', index=False)
        except Exception as e:
            print(f"Unexpected error processing {idx}: {e}")

print("Labeling completed.")
df.to_csv('Data/cleaned_labeled.csv', index=False)
