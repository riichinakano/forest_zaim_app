import pandas as pd
import os
import sys

# UTF-8出力設定
sys.stdout.reconfigure(encoding='utf-8')

# 科目マスタを読み込み
master_df = pd.read_csv('config/account_master.csv', encoding='utf-8')
master_codes = set(master_df['科目コード'].unique())

# 実データから全科目を集計
data_dir = "data/monthly_pl"
years = ['H27', 'H28', 'H29', 'H30', 'H31', 'R2', 'R3', 'R4', 'R5', 'R6']

all_data_codes = {}
for year in years:
    filepath = os.path.join(data_dir, f"{year}_monthly.csv")
    if os.path.exists(filepath):
        df = pd.read_csv(filepath, encoding='shift-jis')
        for _, row in df.iterrows():
            code = row['科目コード']
            name = row['科目名称']
            if code not in all_data_codes:
                all_data_codes[code] = name

data_codes = set(all_data_codes.keys())

# 比較分析
print("=" * 80)
print("科目マスタと実データの比較")
print("=" * 80)

# マスタにあってデータにない科目
master_only = master_codes - data_codes
if master_only:
    print("\n【マスタにあるが実データにない科目】")
    for code in sorted(master_only):
        name = master_df[master_df['科目コード'] == code]['科目名'].iloc[0]
        print(f"  {code}: {name}")
else:
    print("\n【マスタにあるが実データにない科目】 なし ✓")

# データにあってマスタにない科目
data_only = data_codes - master_codes
if data_only:
    print("\n【実データにあるがマスタにない科目】 WARNING")
    for code in sorted(data_only):
        name = all_data_codes[code]
        print(f"  {code}: {name}")
else:
    print("\n【実データにあるがマスタにない科目】 なし OK")

# 共通科目
common = master_codes & data_codes
print(f"\n【共通科目数】 {len(common)}/{len(master_codes)} (マスタ基準)")

# 統計情報
print("\n" + "=" * 80)
print("統計情報")
print("=" * 80)
print(f"科目マスタ登録数: {len(master_codes)}")
print(f"実データ科目数: {len(data_codes)}")
print(f"共通科目数: {len(common)}")
print(f"マスタのみ: {len(master_only)}")
print(f"データのみ: {len(data_only)}")

# 詳細: データのみの科目を年度別に表示
if data_only:
    print("\n" + "=" * 80)
    print("【データのみの科目】詳細（年度別出現状況）")
    print("=" * 80)

    for code in sorted(data_only):
        name = all_data_codes[code]
        # この科目が出現する年度をチェック
        years_list = []
        for year in years:
            filepath = os.path.join(data_dir, f"{year}_monthly.csv")
            if os.path.exists(filepath):
                df = pd.read_csv(filepath, encoding='shift-jis')
                if code in df['科目コード'].values:
                    years_list.append(year)

        years_str = ', '.join(years_list)
        print(f"{code:4d} | {name:25s} | 出現年度: {years_str}")
