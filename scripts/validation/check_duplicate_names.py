import pandas as pd
import os
import sys

# UTF-8出力設定
sys.stdout.reconfigure(encoding='utf-8')

# 実データから全科目を集計
data_dir = "data/monthly_pl"
years = ['H27', 'H28', 'H29', 'H30', 'H31', 'R2', 'R3', 'R4', 'R5', 'R6']

all_accounts = {}
for year in years:
    filepath = os.path.join(data_dir, f"{year}_monthly.csv")
    if os.path.exists(filepath):
        df = pd.read_csv(filepath, encoding='shift-jis')
        for _, row in df.iterrows():
            code = row['科目コード']
            name = row['科目名称']

            if code not in all_accounts:
                all_accounts[code] = {
                    'name': name,
                    'years': []
                }
            all_accounts[code]['years'].append(year)

# 科目名称でグループ化
name_to_codes = {}
for code, info in all_accounts.items():
    name = info['name']
    if name not in name_to_codes:
        name_to_codes[name] = []
    name_to_codes[name].append({
        'code': code,
        'years': info['years']
    })

# 同一名称で複数コードがある科目を抽出
duplicates = {name: codes for name, codes in name_to_codes.items() if len(codes) > 1}

print("=" * 80)
print("同一科目名称で複数の科目コードが存在するケース")
print("=" * 80)

if duplicates:
    for name in sorted(duplicates.keys()):
        codes_info = duplicates[name]
        print(f"\n【科目名称: {name}】")

        for item in sorted(codes_info, key=lambda x: x['code']):
            code = item['code']
            years_list = sorted(set(item['years']))
            years_str = ', '.join(years_list)
            print(f"  コード {code:4d} | 出現年度: {years_str}")

        # 統一可能性の分析
        all_years = set()
        for item in codes_info:
            all_years.update(item['years'])

        # 年度の重複チェック
        year_overlap = False
        for year in all_years:
            count = sum(1 for item in codes_info if year in item['years'])
            if count > 1:
                year_overlap = True
                break

        if year_overlap:
            print("  ⚠️ 同一年度内で複数コードが使用されています（統一には注意が必要）")
        else:
            print("  ✓ 年度が重複していないため、統一可能です")
else:
    print("\n同一名称で複数コードの科目は見つかりませんでした。")

print("\n" + "=" * 80)
print(f"重複科目名の数: {len(duplicates)}")
print("=" * 80)

# 科目マスタの重複もチェック
print("\n" + "=" * 80)
print("科目マスタ内の重複チェック")
print("=" * 80)

master_df = pd.read_csv('config/account_master.csv', encoding='utf-8')
master_name_counts = master_df.groupby('科目名').size()
master_duplicates = master_name_counts[master_name_counts > 1]

if len(master_duplicates) > 0:
    print("\n科目マスタ内で同一名称の科目:")
    for name, count in master_duplicates.items():
        print(f"\n【{name}】 ({count}件)")
        subset = master_df[master_df['科目名'] == name][['科目コード', '科目名', '大分類', '中分類']]
        print(subset.to_string(index=False))
else:
    print("\n科目マスタ内に同一名称の重複はありません。")
