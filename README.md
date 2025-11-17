# Updating Alipay and Wechat data Procedure

## Getting your data

Store the csv files under the folder ./Data/Alipy/ and ./Data/Wechat/, you may name them as 0714.csv if they terminate at 14th July.

## Merging and Cleaning
```zsh
cd Code
python alipy_wechat_update.py
python clean.py
```
this will merge alipay and wechat data with the previous data and store them in ./Data/update/alipay_wechat_uptodate.csv and ./Data/update/cleaned.csv, the latter is the cleaned version.

## Labeling using GPT
Open GPT_labeling.ipynb
Run all
the clean.csv and cleaned_labeled.csv will first be merged, the 'new_category' value in cleaned_labeled.csv will be given to clean.csv, the rest are new data, they need to be fed to GPT.
cleaned_labeled.csv is your final result.