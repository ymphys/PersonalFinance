import pandas as pd
import os

def load_and_concat_csv(dir_path, skiprows, encoding=None):
    csv_files = [f for f in os.listdir(dir_path) if f.endswith('.csv')]
    df_list = [
        pd.read_csv(os.path.join(dir_path, f), skiprows=skiprows, encoding=encoding) 
        for f in csv_files
    ]
    return pd.concat(df_list, ignore_index=True)

def clean_and_export(
    all_data, rename_dict, drop_cols, column_order, 
    output_path, inout_map, amount_clean=False, add_account=False
):
    all_data = all_data.rename(columns=rename_dict)
    if add_account and 'Counterparty_Account' not in all_data.columns:
        all_data['Counterparty_Account'] = '/'
    all_data['DateTime'] = pd.to_datetime(all_data['Date'], errors='coerce')
    all_data['Date'] = all_data['DateTime'].dt.date
    all_data['Time'] = all_data['DateTime'].dt.time
    all_data = all_data.sort_values(['Date', 'Time'], ascending=[True, True])
    for col in drop_cols + ['DateTime']:
        if col in all_data.columns:
            all_data = all_data.drop(columns=[col])
    if amount_clean and 'Amount' in all_data.columns:
        all_data['Amount'] = all_data['Amount'].astype(str).str.replace('¥', '', regex=False).astype(float)
    all_data['in/out'] = all_data['in/out'].map(inout_map)
    all_data = all_data[[col for col in column_order if col in all_data.columns]]
    all_data.to_csv(output_path, index=False)

def process_alipay():
    rename_dict = {
        '交易时间': 'Date',
        '交易分类': 'Category',
        '收/支': 'in/out',
        '金额': 'Amount',
        '交易状态': 'Status',
        '备注': 'Note',
        '交易对方': 'Counterparty',
        '对方账号': 'Counterparty_Account',
        '商品说明': 'Product_Description',
        '收/付款方式': 'Payment_Method'
    }
    drop_cols = ['交易订单号', '商家订单号', 'Unnamed: 12']
    column_order = [
        'Date', 'Time', 'Category', 'in/out', 'Amount', 'Product_Description', 'Status', 'Note',
        'Counterparty', 'Counterparty_Account', 'Payment_Method'
    ]
    inout_map = {'不计收支': 0, '收入': -1, '支出': 1}
    all_data = load_and_concat_csv('Data/Alipay/', skiprows=24, encoding='gb18030')
    clean_and_export(
        all_data, rename_dict, drop_cols, column_order,
        'Data/Alipay/alipay_uptodate.csv', inout_map
    )
    print("Alipay data processed and saved.")

def process_wechat():
    rename_dict = {
        '交易时间': 'Date',
        '交易类型': 'Category',
        '收/支': 'in/out',
        '金额(元)': 'Amount',
        '备注': 'Note',
        '交易对方': 'Counterparty',
        '商品': 'Product_Description',
        '支付方式': 'Payment_Method',
        '当前状态': 'Status',
    }
    drop_cols = ['交易单号', '商户单号']
    column_order = [
        'Date', 'Time', 'Category', 'in/out', 'Amount', 'Product_Description', 'Status', 'Note',
        'Counterparty', 'Counterparty_Account', 'Payment_Method'
    ]
    inout_map = {'/': 0, '收入': -1, '支出': 1}
    all_data = load_and_concat_csv('Data/Wechat/', skiprows=16)
    clean_and_export(
        all_data, rename_dict, drop_cols, column_order,
        'Data/Wechat/wechat_uptodate.csv', inout_map,
        amount_clean=True, add_account=True
    )
    print("Wechat data processed and saved.")

def concat_and_sort():
    alipay_path = 'Data/Alipay/alipay_uptodate.csv'
    wechat_path = 'Data/Wechat/wechat_uptodate.csv'
    previous_path = 'Data/update/alipay_wechat_uptodate.csv'
    df_alipay = pd.read_csv(alipay_path)
    df_wechat = pd.read_csv(wechat_path)
    df_previous = pd.read_csv(previous_path)
    df = pd.concat([df_alipay, df_wechat, df_previous], ignore_index=True)
    # 确保Date和Time为正确类型
    # df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
    # df['Time'] = pd.to_datetime(df['Time'], errors='coerce').dt.time
    df = df.sort_values(['Date', 'Time'], ascending=[True, True])
    df.drop_duplicates(inplace=True)
    df['in/out'] = pd.to_numeric(df['in/out'], errors='coerce').astype('Int64')
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').astype('Float64')
    df.to_csv('Data/update/alipay_wechat_uptodate.csv', index=False)
    print("Alipay & Wechat data merged and saved.")

if __name__ == "__main__":
    process_alipay()
    process_wechat()
    concat_and_sort()