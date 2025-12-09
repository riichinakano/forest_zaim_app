# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# 林業財務分析アプリ (forest_zaim_app) - 開発指示書

## プロジェクト概要

**目的:**
月次損益計算書データを可視化し、複数年度の推移を分析するStreamlitアプリケーション

**ユーザー:**
林業経営者（小規模事業者）

**実装済み機能:**
1. 月次推移グラフ表示（Plotly折れ線グラフ）
2. 複数年度比較（最大5年度）
3. **3階層の集計機能**:
   - 個別科目（例: 売上高、役員報酬）
   - 中分類合算（製造原価、販管費、営業外収益、営業外費用、特別損失）
   - 大分類合算（収益、費用）
4. データテーブル表示（年間合計・前年比・月度平均）
5. CSV/Excelエクスポート

## コマンド

```bash
# アプリの起動
streamlit run app.py

# 依存関係のインストール
pip install -r requirements.txt

# データ検証スクリプト（開発・保守時）
python scripts/validation/check_accounts.py
python scripts/validation/compare_accounts.py
```

## 重要なアーキテクチャパターン

### 1. 3階層データ集計パターン

このアプリケーションは**個別科目 → 中分類 → 大分類**の3階層で集計を行います。`visualizer.py`の`create_monthly_trend_chart()`と`create_comparison_table()`は、この3パターンの処理を含んでいます。

```python
# visualizer.pyでの実装パターン（重要!）
for year in years:
    # パターン1: 中分類での合算（subcategory_filter使用）
    if subcategory_filter and df_master is not None:
        category_codes = df_master[df_master['中分類'] == subcategory_filter]['科目コード'].tolist()
        year_data = df[(df['年度'] == year) & (df['科目コード'].isin(category_codes))]

        # ここで必ずyear_dataのemptyチェックとrow初期化を行う
        if year_data.empty:
            continue

        row = {'年度': year}  # ← この初期化を忘れるとUnboundLocalError

        # 月次データを合算
        for month in months:
            total = year_data[month].sum()
            row[month] = total

        row['年間合計'] = year_data['年間合計'].sum()

    # パターン2: 大分類での合算（category_filter使用）
    elif category_filter and df_master is not None:
        # 同様の処理

    # パターン3: 個別科目（account_code使用）
    else:
        year_data = df[(df['年度'] == year) & (df['科目コード'] == account_code)]
        # ...
```

**重要な注意点:**
- 各パターンで**必ず`row`変数を初期化**すること
- `year_data.empty`のチェック後、`continue`する前に`row`を初期化してはいけない
- この3つのif-elif-else構造は、`create_monthly_trend_chart()`と`create_comparison_table()`の**両方**に存在する

### 2. 年度ソートアルゴリズム

平成（H）と令和（R）が混在するため、文字列ソートではなく特殊なソートが必要です。

```python
# data_loader.py: sort_years()
def sort_years(years: List[str]) -> List[str]:
    """年度を正しい順序でソート（平成→令和）"""
    heisei = sorted([y for y in years if y.startswith('H')],
                    key=lambda x: int(x[1:]))
    reiwa = sorted([y for y in years if y.startswith('R')],
                   key=lambda x: int(x[1:]))
    return heisei + reiwa

# 使用例:
# ['R6', 'H27', 'R5'] → ['H27', 'R5', 'R6']
```

**重要:** `"R10" < "R2"`になる問題を防ぐため、数値部分を`int()`で比較しています。

### 3. エンコーディング処理

**月次データCSV（Shift-JIS） vs 科目マスタ（UTF-8）**

```python
# 月次データ: Shift-JIS（仕様で決定）
df = pd.read_csv(csv_path, encoding='shift-jis')

# 科目マスタ: UTF-8推奨、フォールバックあり
try:
    df = pd.read_csv(master_path, encoding='utf-8')
except UnicodeDecodeError:
    df = pd.read_csv(master_path, encoding='shift-jis')
```

### 4. 製造原価 vs 販管費の分離

**重要な仕様:** 同一科目名でも製造原価と販管費は**統一しない**

例:
- `修繕費 (546)` - 製造原価
- `修繕費 (632)` - 販管費

これらは会計上の分類が異なるため、別科目として扱います。

## データ仕様

### CSVファイル形式

**ファイル名規則:** `{年度}_monthly.csv` (例: `R6_monthly.csv`, `H27_monthly.csv`)

**列構成:**
```csv
タイトル,科目コード,科目名称,当月迄累計金額,当月迄累計構成比,4月,5月,6月,7月,8月,9月,10月,11月,12月,1月,2月,3月
```

**エンコーディング:** Shift-JIS（必須）

### 科目マスタ（config/account_master.csv）

```csv
科目コード,科目名,大分類,中分類,固定費区分,表示順
410,売上高,収益,売上,変動費,1
620,役員報酬,費用,販管費,固定費,20
```

**エンコーディング:** UTF-8推奨

## モジュール構成

```
modules/
├── data_loader.py      # データ読み込み・前処理
│   ├── load_monthly_data()      # 全年度の月次データ統合
│   ├── load_account_master()    # 科目マスタ読み込み
│   ├── get_available_years()    # 利用可能年度リスト取得
│   └── sort_years()             # 年度ソート（平成→令和）
│
├── visualizer.py       # グラフ・テーブル作成
│   ├── create_monthly_trend_chart()  # 月次推移グラフ（3階層対応）
│   ├── create_comparison_table()     # 年度比較テーブル（3階層対応）
│   ├── format_currency()             # 金額フォーマット
│   └── format_percentage()           # パーセンテージフォーマット
│
└── exporter.py         # CSV/Excelエクスポート
    ├── export_to_csv()           # CSV出力（UTF-8 BOM付き）
    ├── export_to_excel()         # Excel出力（書式設定付き）
    └── create_download_filename() # ダウンロードファイル名生成
```

## よくあるエラーと対処法

### 1. UnboundLocalError: cannot access local variable 'row'

**原因:** `create_monthly_trend_chart()`または`create_comparison_table()`で、中分類・大分類の集計処理を追加した際、`row`変数の初期化を忘れた。

**対処法:**
```python
# 悪い例（エラーになる）
if subcategory_filter and df_master is not None:
    category_codes = df_master[df_master['中分類'] == subcategory_filter]['科目コード'].tolist()
    # rowを初期化していない！
    # 後続の処理でrow['前年比'] = Noneを実行するとエラー

# 良い例
if subcategory_filter and df_master is not None:
    category_codes = df_master[df_master['中分類'] == subcategory_filter]['科目コード'].tolist()
    year_data = df[(df['年度'] == year) & (df['科目コード'].isin(category_codes))]

    if year_data.empty:
        continue

    row = {'年度': year}  # ← 必ず初期化

    for month in months:
        row[month] = year_data[month].sum()

    row['年間合計'] = year_data['年間合計'].sum()
```

### 2. UnicodeDecodeError

**原因:** 月次CSVファイルがShift-JISで保存されているのに、UTF-8で読み込もうとした。

**対処法:**
```python
# 月次データは必ずShift-JIS
df = pd.read_csv(csv_path, encoding='shift-jis')
```

### 3. 年度順序が間違っている

**原因:** 文字列ソートで`"R10" < "R2"`になる。

**対処法:** 必ず`sort_years()`関数を使用する。

### 4. KeyError: '4月'

**原因:** CSVファイルの列名が全角文字でない、またはスペースが入っている。

**対処法:** CSVファイルの列名を確認（`'4月'`, `'5月'`, ...は全角）。

## app.pyでの科目選択実装

```python
# app.py: 科目選択の構造（lines 86-164）
account_options = [
    # 大分類の合算
    {
        'code': 0,
        'name': '大分類：収益（合算）',
        'display': '📊 大分類：収益（合算）',
        'is_summary': True,
        'summary_type': 'category',
        'category_filter': '収益',
        'subcategory_filter': None
    },
    # 中分類の合算
    {
        'code': 0,
        'name': '中分類：製造原価（合算）',
        'display': '📈 中分類：製造原価（合算）',
        'is_summary': True,
        'summary_type': 'subcategory',
        'category_filter': None,
        'subcategory_filter': '製造原価'
    },
    # 個別科目（マスタから生成）
    # ...
]

# 選択された科目の情報を抽出
selected_account = next(
    opt for opt in account_options
    if opt['display'] == selected_account_display
)
account_code = selected_account['code']
category_filter = selected_account.get('category_filter', None)
subcategory_filter = selected_account.get('subcategory_filter', None)
```

**重要:** `category_filter`と`subcategory_filter`を`visualizer.py`の関数に渡すことで、3階層の集計を実現しています。

## 新機能実装時のチェックリスト

新しい集計機能や表示機能を追加する際は、以下を確認してください:

1. [ ] `create_monthly_trend_chart()`と`create_comparison_table()`の**両方**で同じロジックを実装したか
2. [ ] 各集計パターンで`row`変数を正しく初期化したか
3. [ ] `year_data.empty`チェックを行ったか
4. [ ] 年度ソートに`sort_years()`を使用したか
5. [ ] CSVエンコーディングはShift-JISを指定したか
6. [ ] `df_master`が`None`の場合の処理を考慮したか

## データ検証

プロジェクトには`scripts/validation/`フォルダにデータ検証スクリプトがあります。

```bash
# 科目一覧の抽出
python scripts/validation/check_accounts.py

# 科目マスタとの比較
python scripts/validation/compare_accounts.py

# 重複科目名の確認
python scripts/validation/check_duplicate_names.py

# 統一可能性の分析
python scripts/validation/analyze_account_unification.py
```

検証レポートは`scripts/validation/reports/`と`docs/data_validation_report.md`を参照してください。

## Git管理方針

### コミット対象
- ソースコード（*.py）
- 設定ファイル（config/*.csv）
- ドキュメント（docs/*.md, README.md, CLAUDE.md）

### 除外対象（.gitignore）
- 内部データ（data/monthly_pl/*.csv, data/cashflow/*.xlsx）
- Python関連（__pycache__/, *.pyc, venv/）
- IDE設定（.vscode/, .idea/）

## 保守・運用

### データ更新手順
1. 新年度CSVを`data/monthly_pl/`に配置（例: `R7_monthly.csv`）
2. ファイル名が`{年度}_monthly.csv`形式であることを確認
3. エンコーディングがShift-JISであることを確認
4. アプリを再起動（自動で新年度を認識）

### 科目追加手順
1. `config/account_master.csv`に行を追加
2. 表示順を設定
3. アプリを再起動

---

**最終更新:** 2025-12-09
**バージョン:** 1.0.0
