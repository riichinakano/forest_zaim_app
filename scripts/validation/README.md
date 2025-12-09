# データ検証スクリプト

このフォルダには、月次損益データの検証に使用したスクリプトが含まれています。

## スクリプト一覧

### 1. check_accounts.py

**目的**: 全年度のCSVデータから科目コードと科目名称を抽出し、一覧表示

**使用方法**:
```bash
python scripts/validation/check_accounts.py
```

**出力内容**:
- 全科目一覧（科目コード順）
- 各科目の出現年度
- 科目総数
- 年度別科目数

### 2. compare_accounts.py

**目的**: 科目マスタ（config/account_master.csv）と実データの比較

**使用方法**:
```bash
python scripts/validation/compare_accounts.py > scripts/validation/reports/account_comparison_report.txt
```

**出力内容**:
- マスタにあるが実データにない科目
- 実データにあるがマスタにない科目
- 共通科目数
- 統計情報

### 3. check_duplicate_names.py

**目的**: 同一科目名称で複数の科目コードが存在するケースを抽出

**使用方法**:
```bash
python scripts/validation/check_duplicate_names.py > scripts/validation/reports/duplicate_names_report.txt
```

**出力内容**:
- 同一名称で複数コードが存在する科目
- 年度の重複状況
- 統一可能性の判定
- 科目マスタ内の重複チェック

### 4. analyze_account_unification.py

**目的**: 科目コード統一の可能性を詳細分析

**使用方法**:
```bash
python scripts/validation/analyze_account_unification.py > scripts/validation/reports/unification_analysis.txt
```

**出力内容**:
- 年度別の同一科目名で複数コードのケース
- 各科目の金額情報
- 統一の推奨案
- 製造原価 vs 販管費の分類分析

## レポート出力先

検証結果は `reports/` フォルダに保存されます：

- `account_comparison_report.txt` - 科目マスタ比較結果
- `duplicate_names_report.txt` - 重複科目名レポート
- `unification_analysis.txt` - 統一可能性分析レポート

## 実行環境

**必要なライブラリ**:
```bash
pip install pandas
```

**Pythonバージョン**: 3.9以上

## 注意事項

1. **エンコーディング**: CSVファイルはShift-JISで保存されている前提
2. **ファイルパス**: プロジェクトルートから実行することを想定
3. **出力エンコーディング**: UTF-8で出力（`sys.stdout.reconfigure(encoding='utf-8')`）

## 検証結果サマリー

詳細は `../../docs/data_validation_report.md` を参照してください。

### 主要な発見

1. **科目総数**: 80科目（全10年度）
2. **科目マスタとの差分**:
   - マスタのみ: 3科目
   - データのみ: 23科目
3. **重複科目名**: 9種類
   - 製造原価 vs 販管費: 統一すべきでない
   - 年度非重複: 統一可能（ただし現状維持推奨）
4. **推奨アクション**:
   - 9000番台の集計科目をマスタに追加
   - 科目コードは現状維持

---

**作成日**: 2025-12-08
**最終更新**: 2025-12-08
