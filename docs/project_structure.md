# プロジェクト構造

林業財務分析アプリ（forest_zaim_app）のディレクトリ構造です。

## ディレクトリ構成

```
forest_zaim_app/
│
├── app.py                          # メインアプリケーション（Streamlit）
├── requirements.txt                # 依存ライブラリ
├── README.md                       # ユーザー向け説明書
├── CLAUDE.md                       # 開発者向け指示書
├── .gitignore                      # Git除外設定
│
├── config/                         # 設定ファイル
│   └── account_master.csv          # 科目マスタ（60科目登録）
│
├── data/                           # データフォルダ
│   ├── monthly_pl/                 # 月次損益データ
│   │   ├── README.md               # データ配置方法の説明
│   │   ├── H27_monthly.csv         # 平成27年度（.gitignore除外）
│   │   ├── H28_monthly.csv         # 平成28年度（.gitignore除外）
│   │   ├── H29_monthly.csv         # 平成29年度（.gitignore除外）
│   │   ├── H30_monthly.csv         # 平成30年度（.gitignore除外）
│   │   ├── H31_monthly.csv         # 平成31年度/令和元年度（.gitignore除外）
│   │   ├── R2_monthly.csv          # 令和2年度（.gitignore除外）
│   │   ├── R3_monthly.csv          # 令和3年度（.gitignore除外）
│   │   ├── R4_monthly.csv          # 令和4年度（.gitignore除外）
│   │   ├── R5_monthly.csv          # 令和5年度（.gitignore除外）
│   │   └── R6_monthly.csv          # 令和6年度（.gitignore除外）
│   │
│   └── cashflow/                   # キャッシュフローデータ（将来用）
│       └── README.md               # データ配置方法の説明
│
├── modules/                        # Pythonモジュール
│   ├── __init__.py
│   ├── data_loader.py              # データ読み込みモジュール
│   ├── visualizer.py               # グラフ描画モジュール（未実装）
│   ├── exporter.py                 # エクスポートモジュール（未実装）
│   ├── cashflow_loader.py          # キャッシュフロー読込（実験中）
│   └── cashflow_visualizer.py      # キャッシュフロー可視化（実験中）
│
├── scripts/                        # ユーティリティスクリプト
│   └── validation/                 # データ検証スクリプト
│       ├── README.md               # スクリプト説明
│       ├── check_accounts.py       # 科目一覧抽出
│       ├── compare_accounts.py     # 科目マスタ比較
│       ├── check_duplicate_names.py # 重複科目抽出
│       ├── analyze_account_unification.py # 統一可能性分析
│       └── reports/                # 検証レポート出力先
│           ├── account_comparison_report.txt
│           ├── duplicate_names_report.txt
│           └── unification_analysis.txt
│
└── docs/                           # ドキュメント
    ├── README.md                   # ドキュメント一覧
    ├── data_validation_report.md   # データ検証レポート
    └── project_structure.md        # このファイル
```

## ファイル説明

### ルートディレクトリ

| ファイル | 説明 | 用途 |
|---------|------|------|
| `app.py` | メインアプリケーション | Streamlitアプリのエントリポイント |
| `requirements.txt` | 依存ライブラリ | pip install時に使用 |
| `README.md` | ユーザー向け説明書 | アプリの使い方、セットアップ方法 |
| `CLAUDE.md` | 開発者向け指示書 | Claude Codeを使った開発指針 |
| `.gitignore` | Git除外設定 | 内部データやキャッシュファイルを除外 |

### config/

| ファイル | 説明 | エンコーディング |
|---------|------|----------------|
| `account_master.csv` | 科目マスタ | UTF-8 |

**列構成**:
- 科目コード, 科目名, 大分類, 中分類, 固定費区分, 表示順

### data/monthly_pl/

月次損益計算書のCSVファイルを格納。

**ファイル形式**:
- **エンコーディング**: Shift-JIS
- **列構成**: タイトル, 科目コード, 科目名称, 当月迄累計金額, 当月迄累計構成比, 4月〜3月

**注意**: CSVファイルは`.gitignore`で除外され、GitHubにコミットされません。

### data/cashflow/

キャッシュフローデータを格納（将来の機能拡張用）。

### modules/

Pythonモジュール群。

| ファイル | 説明 | ステータス |
|---------|------|----------|
| `data_loader.py` | データ読み込み | 実装済み |
| `visualizer.py` | グラフ描画 | 未実装 |
| `exporter.py` | エクスポート | 未実装 |
| `cashflow_loader.py` | キャッシュフロー読込 | 実験中 |
| `cashflow_visualizer.py` | キャッシュフロー可視化 | 実験中 |

### scripts/validation/

データ検証用スクリプト。開発・保守時に使用。

| スクリプト | 説明 |
|-----------|------|
| `check_accounts.py` | 全科目の一覧を抽出 |
| `compare_accounts.py` | 科目マスタとの比較 |
| `check_duplicate_names.py` | 重複科目名の抽出 |
| `analyze_account_unification.py` | 統一可能性の分析 |

### docs/

プロジェクトドキュメント。

| ファイル | 説明 |
|---------|------|
| `README.md` | ドキュメント一覧 |
| `data_validation_report.md` | データ検証レポート（2025-12-08作成） |
| `project_structure.md` | このファイル |

## データフロー

```
CSVファイル (Shift-JIS)
    ↓
data_loader.py
    ↓
pandas DataFrame
    ↓
app.py (Streamlit)
    ↓
visualizer.py (Plotly)
    ↓
ブラウザ表示
```

## Git管理方針

### コミット対象

- ソースコード（*.py）
- 設定ファイル（config/*.csv）
- ドキュメント（docs/*.md, README.md, CLAUDE.md）
- READMEファイル（data/*/README.md）

### 除外対象（.gitignore）

- 内部データ（data/monthly_pl/*.csv, data/cashflow/*.xlsx）
- Python関連（__pycache__/, *.pyc, venv/）
- IDE設定（.vscode/, .idea/）
- OS関連（.DS_Store, Thumbs.db, nul）
- ログファイル（*.log）

## 開発環境

**Python**: 3.9以上

**主要ライブラリ**:
- streamlit >= 1.28.0
- pandas >= 2.0.0
- plotly >= 5.17.0
- openpyxl >= 3.1.0

**インストール**:
```bash
pip install -r requirements.txt
```

**起動**:
```bash
streamlit run app.py
```

---

**作成日**: 2025-12-08
**最終更新**: 2025-12-08
