import pandas as pd
import requests
import time
import json
from tqdm import tqdm
import os


def prepare_batch_prompt(batch_df):
    """准备发送给DeepSeek API的prompt"""
    examples = []
    for _, row in batch_df.iterrows():
        examples.append(
            f"Date: {row['Date']}, Time: {row['Time']}, "
            f"Amount: {row['Amount']}, Desc: {row['Product_Description']}, "
            f"Counterparty: {row['Counterparty']}, Payment: {row['Payment_Method']}"
        )
    return "\n".join(examples)

def call_deepseek_api(prompt_text):
    """调用DeepSeek API获取分类结果"""
    headers = {
        'Authorization': f'Bearer {os.getenv("DEEPSEEK_API_KEY")}',
        'Content-Type': 'application/json'
    }
    
    system_prompt = """你是一个专业的消费记录分类助手。请根据以下消费记录的各字段值，给出最精确的分类标签(New_Category):
- 餐饮类: food(正餐), drink(饮料), snacks(零食)，并考虑时间特征(早餐/午餐/晚餐)
- 交通类: public_transport(公交地铁), taxi(打车), car_rental(租车), train(火车), flight(飞机) 
- 酒店旅游: hotel(住宿), ticket(门票)
- 其他类别保持原有分类但统一英文命名
- 只返回分类结果，每行一个"""

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.3
    }

    try:
        response = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return [line.strip() for line in response.json()['choices'][0]['message']['content'].split('\n') if line.strip()]
    except Exception as e:
        print(f"API调用失败: {e}")
        return None

def process_csv_with_deepseek(input_csv, output_csv, batch_size=20):
    """主处理函数"""
    df = pd.read_csv(input_csv)
    
    results = []
    total_batches = (len(df) // batch_size) + 1
    
    for i in tqdm(range(0, len(df), batch_size)):
        batch = df.iloc[i:i+batch_size]
        prompt = prepare_batch_prompt(batch)
        
        # 调用API并处理结果
        classifications = None
        retries = 3
        while retries > 0 and not classifications:
            classifications = call_deepseek_api(prompt)
            if not classifications:
                retries -= 1
                time.sleep(2)
        
        if classifications and len(classifications) == len(batch):
            results.extend(classifications)
        else:
            print(f"批处理 {i//batch_size + 1}/{total_batches} 失败，使用原始分类")
            results.extend(batch['Category'].tolist())
        
        # 每5批保存一次进度
        if i > 0 and i % (5*batch_size) == 0:
            temp_df = df.copy()
            temp_df['New_Category'] = results + ['pending']*(len(df)-len(results))
            temp_df.to_csv(output_csv, index=False)
    
    # 保存最终结果
    df['New_Category'] = results
    df.to_csv(output_csv, index=False)
    print(f"处理完成，结果已保存到 {output_csv}")

if __name__ == '__main__':
    # 配置参数
    INPUT_FILE = "Data/update/202505272148.csv"
    OUTPUT_FILE = "Data/update/categorized.csv"
    
    # 执行处理
    process_csv_with_deepseek(INPUT_FILE, OUTPUT_FILE)