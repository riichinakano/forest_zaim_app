# 林業財務分析アプリ (forest_zaim_app) - 開発指示書

このドキュメントは、Claude Codeを使用して本アプリケーションを開発・保守する際の指針です。

## プロジェクト概要

**目的:**  
月次損益計算書データを可視化し、複数年度の推移を分析するStreamlitアプリケーション

**ユーザー:**  
林業経営者（小規模事業者）

**主要機能:**
1. 月次推移グラフ表示（Plotly折れ線グラフ）
2. 複数年度比較（最大5年度）
3. 科目別分析（収益・製造原価・販管費）
4. データテーブル表示（年間合計・前年比）
5. CSV/Excelエクスポート

## 開発環境

```bash
Python: 3.9以上
主要ライブラリ:
  - streamlit>=1.28.0
  - pandas>=2.0.0
  - plotly>=5.17.0
  - openpyxl>=3.1.0
```

## ファイル構成

```
forest_zaim_app/
├── app.py                      # メインアプリケーション
├── requirements.txt            # 依存ライブラリ
├── README.md                   # ユーザー向け説明書
├── CLAUDE.md                   # 本ファイル（開発者向け）
├── modules/
│   ├── __init__.py
│   ├── data_loader.py         # データ読み込みモジュール
│   ├── visualizer.py          # グラフ描画モジュール
│   └── exporter.py            # エクスポートモジュール
├── config/
│   └── account_master.csv     # 勘定科目マスタ
└── data/
    └── monthly_pl/
        ├── H27_monthly.csv    # 平成27年度データ
        ├── ...
        └── R6_monthly.csv     # 令和6年度データ
```

## データ仕様

### CSVファイル形式

**ファイル名規則:**
```
{年度}_monthly.csv
例: R6_monthly.csv, H27_monthly.csv
```

**列構成:**
```csv
タイトル,科目コード,科目名称,当月迄累計金額,当月迄累計構成比,4月,5月,6月,7月,8月,9月,10月,11月,12月,1月,2月,3月
```

**データ型:**
- タイトル: str (固定値 "損益計算書")
- 科目コード: int (例: 410, 620)
- 科目名称: str (例: "売上高", "役員報酬")
- 当月迄累計金額: int (年間合計)
- 当月迄累計構成比: float (構成比%)
- 4月〜3月: int (各月の金額)

**エンコーディング:** Shift-JIS (重要!)

### 科目マスタ

**ファイル:** `config/account_master.csv`

```csv
科目コード,科目名,大分類,中分類,固定費区分,表示順
410,売上高,収益,売上,変動費,1
812,Jクレジット収入,収益,営業外収益,その他,2
819,雑収入,収益,営業外収益,その他,3
620,役員報酬,費用,販管費,固定費,20
621,給料手当,費用,販管費,固定費,21
```

## モジュール設計

### 1. data_loader.py

**責務:** データの読み込みと前処理

**主要関数:**

```python
def load_monthly_data(data_dir: str = "data/monthly_pl") -> pd.DataFrame:
    """
    全年度の月次データを読み込み、統合したDataFrameを返す
    
    Returns:
        pd.DataFrame: 列 ['年度', '科目コード', '科目名称', '4月', ..., '3月', '年間合計']
    """
    
def load_account_master(config_dir: str = "config") -> pd.DataFrame:
    """
    科目マスタを読み込む
    
    Returns:
        pd.DataFrame: 科目情報（コード、名称、分類等）
    """
    
def get_available_years(data_dir: str = "data/monthly_pl") -> list:
    """
    利用可能な年度のリストを返す
    
    Returns:
        list: ['H27', 'H28', ..., 'R6']
    """
```

**実装時の注意点:**
- CSVのエンコーディングは必ずShift-JISで読み込む
- ファイル名から年度を抽出（例: "R6_monthly.csv" → "R6"）
- 欠損値は0で埋める
- 年度順にソート（H27, H28, ..., R1, R2, ...）

**年度ソートの実装:**
```python
def sort_years(years: list) -> list:
    """年度を正しい順序でソート（平成→令和）"""
    heisei = sorted([y for y in years if y.startswith('H')], 
                    key=lambda x: int(x[1:]))
    reiwa = sorted([y for y in years if y.startswith('R')], 
                   key=lambda x: int(x[1:]))
    return heisei + reiwa
```

### 2. visualizer.py

**責務:** グラフの作成

**主要関数:**

```python
def create_monthly_trend_chart(
    df: pd.DataFrame,
    account_code: int,
    years: list,
    account_name: str = None
) -> go.Figure:
    """
    月次推移の折れ線グラフを作成
    
    Args:
        df: 月次データ（data_loaderの出力）
        account_code: 科目コード
        years: 表示する年度のリスト
        account_name: 科目名（グラフタイトル用）
    
    Returns:
        plotly.graph_objects.Figure
    """
```

**グラフ仕様:**
- X軸: 月次（4月〜3月）
- Y軸: 金額（万円単位で表示）
- 凡例: 年度ごとに色分け
- ホバーテキスト: "{年度} {月}: {金額:,}円"
- インタラクション: ズーム、パン有効

**色設定:**
```python
YEAR_COLORS = {
    'H27': '#8c564b',
    'H28': '#e377c2',
    'H29': '#7f7f7f',
    'H30': '#bcbd22',
    'R1': '#17becf',
    'R2': '#9467bd',
    'R3': '#d62728',
    'R4': '#1f77b4',
    'R5': '#2ca02c',
    'R6': '#ff7f0e',
}
```

### 3. exporter.py

**責務:** データのエクスポート

**主要関数:**

```python
def export_to_csv(df: pd.DataFrame, filename: str = None) -> bytes:
    """
    DataFrameをCSV形式でエクスポート
    
    Returns:
        bytes: CSV data (UTF-8 BOM付き、Excel対応)
    """

def export_to_excel(
    df: pd.DataFrame,
    filename: str = None,
    sheet_name: str = "月次推移"
) -> bytes:
    """
    DataFrameをExcel形式でエクスポート（書式設定付き）
    
    Returns:
        bytes: Excel data
    """
```

**Excel書式設定:**
- ヘッダー行: 太字、背景色（薄緑）
- 数値: 3桁カンマ区切り
- 年間合計列: 太字
- 前年比: パーセント表示、色分け（増加=緑、減少=赤）

### 4. app.py

**責務:** StreamlitUIとアプリケーション制御

**構成:**

```python
# ページ設定
st.set_page_config(
    page_title="林業財務分析",
    page_icon="📊",
    layout="wide"
)

# サイドバー
with st.sidebar:
    - 科目選択（ドロップダウン）
    - 年度選択（マルチセレクト、最大5年度）
    - エクスポートボタン

# メインエリア
- タイトル・説明
- グラフ表示
- データテーブル表示
```

**実装時の注意点:**
- `@st.cache_data`でデータ読み込みをキャッシュ
- エラーハンドリング（ファイル未存在時等）
- ローディング表示（`st.spinner`）
- 選択年度が0の場合のエラーメッセージ

## 実装手順

### Phase 1: 基本機能実装

```bash
# 1. プロジェクト構造作成
mkdir -p forest_zaim_app/{modules,config,data/monthly_pl}
cd forest_zaim_app

# 2. 依存ライブラリインストール
pip install -r requirements.txt

# 3. モジュール実装
# modules/__init__.py
# modules/data_loader.py
# modules/visualizer.py
# modules/exporter.py

# 4. 科目マスタ作成
# config/account_master.csv

# 5. メインアプリ実装
# app.py

# 6. 動作確認
streamlit run app.py
```

### テストデータ準備

開発時は以下の最小構成でテスト：

```
data/monthly_pl/
├── R5_monthly.csv
└── R6_monthly.csv
```

## 動作確認項目

### 基本機能
- [ ] データ読み込み（全年度）
- [ ] 科目選択（収益科目）
- [ ] 年度選択（1年度）
- [ ] グラフ表示
- [ ] データテーブル表示

### 複数年度比較
- [ ] 年度選択（2年度以上）
- [ ] グラフ重ね表示
- [ ] 凡例表示
- [ ] 前年比計算

### エクスポート
- [ ] CSV出力
- [ ] Excel出力
- [ ] ファイル名生成

### エラーハンドリング
- [ ] データファイル未存在時
- [ ] 年度未選択時
- [ ] 科目コード不一致時

## トラブルシューティング

### よくあるエラーと対処法

**1. UnicodeDecodeError**
```python
# 原因: CSVのエンコーディング指定漏れ
# 対策:
pd.read_csv(filepath, encoding='shift-jis')
```

**2. KeyError: '4月'**
```python
# 原因: 列名に全角数字が使われていない
# 対策: CSVファイルの列名を確認
```

**3. グラフが表示されない**
```python
# 原因: データが空、または年度選択なし
# 対策: データ存在チェックを追加
if df.empty or not selected_years:
    st.warning("データを選択してください")
    st.stop()
```

**4. 年度順序が正しくない**
```python
# 原因: 文字列ソートで "R10" < "R2" になる
# 対策: sort_years()関数を使用
```

## パフォーマンス最適化

### キャッシュ戦略

```python
@st.cache_data(ttl=3600)  # 1時間キャッシュ
def load_all_data():
    return load_monthly_data()

@st.cache_data
def load_master():
    return load_account_master()
```

### メモリ管理

- 大量年度選択時のメモリ使用量に注意
- 必要な列のみをDataFrameに保持
- 不要なデータは適宜削除

## 拡張機能（Phase 2以降）

### 予定機能
1. 限界利益分析（Tab 2）
2. キャッシュフロー予測
3. 月次アラート機能
4. 複数科目同時表示
5. レポート自動生成

### データ拡張
- 資金繰り表データの統合
- 予算vs実績比較
- 前年同月比較

## コーディング規約

### 命名規則
- 関数: snake_case
- クラス: PascalCase
- 定数: UPPER_SNAKE_CASE
- プライベート: _prefix

### ドキュメンテーション
- 全関数にdocstring必須
- 複雑なロジックにはコメント
- 型ヒント推奨

### エラーハンドリング
```python
try:
    # 処理
except FileNotFoundError as e:
    st.error(f"ファイルが見つかりません: {e}")
except Exception as e:
    st.error(f"予期しないエラー: {e}")
    st.exception(e)  # デバッグ時のみ
```

## Git運用（推奨）

```bash
# ブランチ戦略
main       # 本番環境
develop    # 開発環境
feature/*  # 機能追加

# コミットメッセージ
feat: 新機能追加
fix: バグ修正
docs: ドキュメント更新
refactor: リファクタリング
test: テスト追加
```

## デプロイ

### ローカル環境
```bash
streamlit run app.py
```

### Streamlit Cloud（オプション）
1. GitHubにpush
2. Streamlit Cloudで接続
3. requirements.txt を認識して自動デプロイ

## 保守・運用

### データ更新手順
1. 新年度CSVを `data/monthly_pl/` に配置
2. ファイル名を規則に従う（例: R7_monthly.csv）
3. アプリを再起動（自動で新年度を認識）

### 科目追加手順
1. `config/account_master.csv` に行追加
2. 表示順を設定
3. アプリを再起動

## 問い合わせ先

技術的な質問や機能要望は、Claude Codeセッションで対応します。

---

**最終更新:** 2025-12-08  
**バージョン:** 1.0.0
