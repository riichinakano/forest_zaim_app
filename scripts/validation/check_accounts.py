import pandas as pd
import os

data_dir = "data/monthly_pl"
years = ['H27', 'H28', 'H29', 'H30', 'H31', 'R2', 'R3', 'R4', 'R5', 'R6']

# 全年度の科目を集計
all_accounts = {}

for year in years:
    filepath = os.path.join(data_dir, f"{year}_monthly.csv")
    if os.path.exists(filepath):
        df = pd.read_csv(filepath, encoding='shift-jis')
        accounts = df[['科目コード', '科目名称']].drop_duplicates()

        for _, row in accounts.iterrows():
            code = row['科目コード']
            name = row['科目名称']

            if code not in all_accounts:
                all_accounts[code] = {
                    'name': name,
                    'years': []
                }
            all_accounts[code]['years'].append(year)

# 結果を表示
print("=" * 80)
print("全科目一覧（科目コード順）")
print("=" * 80)

for code in sorted(all_accounts.keys()):
    info = all_accounts[code]
    years_str = ', '.join(info['years'])
    print(f"{code:4d} | {info['name']:20s} | {years_str}")

print("\n" + "=" * 80)
print(f"科目総数: {len(all_accounts)}")
print("=" * 80)

# 年度ごとの科目数
print("\n年度別科目数:")
for year in years:
    filepath = os.path.join(data_dir, f"{year}_monthly.csv")
    if os.path.exists(filepath):
        df = pd.read_csv(filepath, encoding='shift-jis')
        count = df['科目コード'].nunique()
        print(f"{year}: {count}科目")
