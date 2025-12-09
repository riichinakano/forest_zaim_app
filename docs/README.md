# ドキュメント一覧

このフォルダには、林業財務分析アプリに関連するドキュメントが含まれています。

## ドキュメント

### data_validation_report.md

**概要**: 月次損益データの検証レポート

**内容**:
- データ配置状況の確認
- 科目コード・科目名称の検証
- 科目マスタとの比較分析
- 科目コード統一の検討
- 推奨事項

**作成日**: 2025-12-08

**対象データ**: H27年度〜R6年度（全10年度）

---

## 関連ファイル

### プロジェクト構造

```
forest_zaim_app/
├── docs/                           # ドキュメント（このフォルダ）
│   ├── README.md                   # このファイル
│   └── data_validation_report.md   # データ検証レポート
├── scripts/                        # スクリプト
│   └── validation/                 # データ検証スクリプト
│       ├── README.md               # スクリプト説明
│       ├── check_accounts.py       # 科目一覧抽出
│       ├── compare_accounts.py     # マスタ比較
│       ├── check_duplicate_names.py # 重複科目抽出
│       ├── analyze_account_unification.py # 統一可能性分析
│       └── reports/                # 検証レポート出力先
│           ├── account_comparison_report.txt
│           ├── duplicate_names_report.txt
│           └── unification_analysis.txt
├── data/                           # データフォルダ
│   └── monthly_pl/                 # 月次損益データ
│       ├── README.md               # データ配置方法
│       └── *.csv                   # 年度別CSVファイル（.gitignore除外）
├── config/                         # 設定ファイル
│   └── account_master.csv          # 科目マスタ
└── CLAUDE.md                       # 開発指示書
```

---

**最終更新**: 2025-12-08
