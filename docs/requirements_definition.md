# 林業財務分析アプリ - AIチャット機能 要件定義書

**プロジェクト名**: forest_zaim_app - AIチャット機能追加（Phase 2）  
**作成日**: 2025-12-11  
**対象環境**: VS Code + Claude Code  
**実装担当**: Claude Code

---

## 1. プロジェク概要

### 1.1 目的
既存の財務分析アプリ（PL/BS可視化）に、自然言語で財務データを分析できるAIチャット機能を追加する。

### 1.2 背景
- **現状**: 月次PL/BSデータを手動でグラフ化・比較（Phase 1.5完了）
- **課題**: 複雑な財務判断（借入返済額検討、役員報酬決定等）には専門知識が必要
- **解決**: Gemini APIを活用し、自然言語での質問→Python自動実行→回答生成

### 1.3 ユーザー
林業経営者（小規模事業者）

---

## 2. 機能要件

### 2.1 コア機能

#### 2.1.1 AIチャットインターフェース
- **実装場所**: `pages/3_💬_AIチャット.py`（Streamlit Pagesとして独立）
- **UI構成**:
  - サイドバー: モデル選択、参考資料アップロード、設定
  - メインエリア: チャット履歴、入力欄、コード承認UI
- **入力**: テキスト入力欄（`st.chat_input`）
- **出力**: テキスト回答 + Plotlyグラフ + データテーブル

#### 2.1.2 Geminiモデル選択
ユーザーがタスクに応じてモデルを切り替え可能：

| モデル名（UI表示） | APIモデルコード | 用途 |
|---|---|---|
| Gemini 2.5 Flash（バランス・推奨）★ | `gemini-2.5-flash` | 汎用的な分析（デフォルト） |
| Gemini 2.5 Pro（高度な分析） | `gemini-2.5-pro` | 複雑な予測・推論が必要な質問 |
| Gemini 2.0 Flash Lite（軽量・高速） | `gemini-2.0-flash-lite` | 過去データ取得のみの簡単な質問 |
| Gemini 3 Pro Preview（最新・実験的） | `gemini-3-pro-preview` | 最新機能のテスト用 |

**実装**: サイドバーでラジオボタン選択

#### 2.1.3 データ参照方式
- **基本方針**: 動的読み込み（Geminiが必要なファイルを判断）
- **対象データ**:
  - `data/monthly_pl/`: H27〜R6の月次PL（10年分）
  - `data/monthly_bs/`: H27〜R6の月次BS（10年分）
  - `config/account_master.csv`: PL科目マスタ
  - `config/bs_account_master.csv`: BS科目マスタ
- **Geminiへの情報提供**:
  ```python
  available_files = {
      "pl": ["H27_monthly.csv", ..., "R6_monthly.csv"],
      "bs": ["H27_monthly_bs.csv", ..., "R6_monthly_bs.csv"],
      "masters": ["account_master.csv", "bs_account_master.csv"]
  }
  ```

#### 2.1.4 参考資料アップロード
- **対応形式**: CSV, Excel (.xlsx)
- **保存先**: `data/uploaded/`（永続化）
- **ファイル名**: タイムスタンプ付き（例: `20251211_143022_資金繰表.xlsx`）
- **Geminiへの渡し方**: ファイルパスのみ渡し、Geminiに読み込みコードを書かせる
- **UI**: サイドバーで`st.file_uploader`（複数ファイル対応）

#### 2.1.5 コード生成・承認・実行
**フロー**:
```
1. ユーザーが質問入力
   ↓
2. Geminiがデータ構造を理解してPythonコード生成
   ↓
3. 安全性チェック（CodeExecutor.validate_code）
   ↓ (NG) → エラー表示 + 自動再生成（最大3回）
   ↓ (OK)
4. st.expanderでコード表示 + 「実行」「キャンセル」ボタン
   ↓
5. ユーザーが「実行」を承認
   ↓
6. サンドボックス環境で実行
   ↓
7. 結果表示（テキスト + グラフ + テーブル）
```

**コード承認UI**:
```python
with st.expander("📝 生成されたコード", expanded=True):
    st.code(generated_code, language="python")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ 実行", type="primary"):
            # 実行処理
    with col2:
        if st.button("❌ キャンセル"):
            # キャンセル処理
```

#### 2.1.6 エラーハンドリング
- **自動修正**: 実行エラー発生時、エラー内容をGeminiにフィードバック→コード再生成→再実行（最大3回まで）
- **対象エラー**: KeyError, ValueError, FileNotFoundError等
- **重大エラー**: SyntaxError等は自動修正せず、ユーザーに通知

#### 2.1.7 グラフ生成・保存
- **描画ライブラリ**: Plotly（既存UI統一）
- **保存形式**: 
  - HTML（インタラクティブ、デフォルト）
  - PNG（静的画像、`kaleido`ライブラリ使用）
- **UI**: サイドバーでマルチセレクト選択
- **保存先**: `notebooks/chat_logs/{セッションID}/`

#### 2.1.8 会話ログ保存
- **保存タイミング**: 「💾 会話を保存」ボタンクリック時（手動）
- **保存場所**: `notebooks/chat_logs/{YYYYMMDD_HHMMSS_テーマ名}/`
- **保存内容**:
  ```
  notebooks/chat_logs/20251211_143022_借入返済額検討/
  ├── conversation.md          # 会話履歴（Markdown形式）
  ├── graph_01.html            # グラフ（HTML）
  ├── graph_01.png             # グラフ（PNG）
  ├── graph_02.html
  ├── graph_02.png
  └── data_snapshot.csv        # 使用したデータのスナップショット
  ```
- **Markdown形式**（Obsidian互換）:
  ```markdown
  # 借入返済額検討
  
  **日時**: 2025-12-11 14:30:22  
  **モデル**: Gemini 2.5 Flash
  
  ---
  
  ## ユーザー
  R6の借入返済額を教えて
  
  ## アシスタント
  R6年度の借入返済額は以下の通りです：
  
  - 長期借入金返済: 12,000,000円
  - 短期借入金返済: 3,500,000円
  - 合計: 15,500,000円
  
  ![グラフ](graph_01.png)
  
  ### 生成されたコード
  ```python
  import pandas as pd
  ...
  ```
  ```

### 2.2 既存機能の改修

#### 2.2.1 app.pyのリファクタリング
- **現状**: `app.py`に全てのコード（PL/BSタブ、約400行）
- **変更後**: Streamlit Pagesに分離
  ```
  pages/
  ├── 1_📊_PL分析.py       # 既存PLタブのコード移行
  ├── 2_💰_BS分析.py       # 既存BSタブのコード移行
  └── 3_💬_AIチャット.py   # 新規
  ```
- **app.py**: 削除または最小限のトップページ化

---

## 3. 非機能要件

### 3.1 セキュリティ

#### 3.1.1 コード実行の安全性
**禁止操作**:
```python
BLOCKED_OPERATIONS = [
    'os.remove',           # ファイル削除禁止
    'shutil.rmtree',       # ディレクトリ削除禁止
    'subprocess',          # 外部プロセス起動禁止
    'eval(',               # 動的評価禁止
    'exec(',               # 動的実行禁止（自身以外）
    '__import__',          # 動的インポート禁止
]
```

**許可される書き込み先**:
```python
ALLOWED_WRITE_DIRS = [
    'notebooks/chat_logs/',    # ログ保存のみ
    'data/uploaded/',          # アップロードファイル保存
]
```

#### 3.1.2 APIキー管理
- **保存場所**: `.env`ファイル
- **環境変数名**: `GEMINI_API_KEY`
- **Git管理**: `.gitignore`に追加済み

### 3.2 パフォーマンス
- **初回起動時間**: 5秒以内（データ読み込みなし）
- **質問応答時間**: 
  - 簡単な質問: 5秒以内（Gemini 2.0 Flash Lite）
  - 複雑な質問: 30秒以内（Gemini 2.5 Pro）
- **メモリ使用量**: 500MB以内（10年分データ読み込み時）

### 3.3 可用性
- **エラー時の動作**: 自動再試行（最大3回）→ユーザーに通知
- **セッション管理**: ブラウザリロード時も会話履歴維持（`st.session_state`）

---

## 4. システム構成

### 4.1 ディレクトリ構成（最終版）

```
forest_zaim_app/
├── .env                            # APIキー（Git管理外）
├── .gitignore                      # 更新必要
├── requirements.txt                # 更新必要（kaleido追加）
├── README.md                       # 更新必要（AIチャット説明追加）
├── CLAUDE.md                       # 更新必要
│
├── app.py                          # 削除またはトップページ化
│
├── pages/                          # 新規ディレクトリ
│   ├── 1_📊_PL分析.py              # 既存のPLタブを移行
│   ├── 2_💰_BS分析.py              # 既存のBSタブを移行
│   └── 3_💬_AIチャット.py          # 新規実装
│
├── modules/
│   ├── __init__.py
│   ├── data_loader.py              # 既存（変更なし）
│   ├── visualizer.py               # 既存（変更なし）
│   ├── exporter.py                 # 既存（変更なし）
│   ├── gemini_chat.py              # 新規
│   └── financial_analyzer.py       # 新規
│
├── config/
│   ├── account_master.csv          # 既存
│   └── bs_account_master.csv       # 既存
│
├── data/
│   ├── monthly_pl/                 # 既存
│   ├── monthly_bs/                 # 既存
│   └── uploaded/                   # 新規（アップロードファイル保存）
│
└── notebooks/
    ├── testnb20251210_01.ipynb     # 既存
    └── chat_logs/                  # 新規（会話ログ保存）
        └── 20251211_143022_借入返済額検討/
            ├── conversation.md
            ├── graph_01.html
            ├── graph_01.png
            └── data_snapshot.csv
```

### 4.2 モジュール設計

#### 4.2.1 modules/gemini_chat.py
```python
"""
Gemini API連携とコード生成・実行を管理
"""

class GeminiClient:
    """Gemini APIクライアント"""
    
    def __init__(self, model_name: str, api_key: str):
        """
        Args:
            model_name: Geminiモデル名（例: "gemini-2.5-flash"）
            api_key: Gemini APIキー
        """
        pass
    
    def generate_code(
        self, 
        user_question: str, 
        available_files: dict,
        uploaded_files: list = None,
        conversation_history: list = None
    ) -> str:
        """
        ユーザーの質問からPythonコードを生成
        
        Args:
            user_question: ユーザーの質問
            available_files: 利用可能なファイル一覧
            uploaded_files: アップロードされたファイルパス一覧
            conversation_history: 会話履歴
            
        Returns:
            生成されたPythonコード
        """
        pass
    
    @staticmethod
    def get_available_models() -> dict:
        """利用可能なモデル一覧を取得"""
        return {
            "Gemini 2.5 Flash（バランス・推奨）": "gemini-2.5-flash",
            "Gemini 2.5 Pro（高度な分析）": "gemini-2.5-pro",
            "Gemini 2.0 Flash Lite（軽量・高速）": "gemini-2.0-flash-lite",
            "Gemini 3 Pro Preview（最新・実験的）": "gemini-3-pro-preview"
        }


class CodeExecutor:
    """生成されたコードの検証・実行"""
    
    @staticmethod
    def validate_code(code: str) -> tuple[bool, str]:
        """
        コードの安全性をチェック
        
        Args:
            code: 検証するPythonコード
            
        Returns:
            (検証結果, エラーメッセージ)
        """
        pass
    
    @staticmethod
    def execute_code(
        code: str, 
        max_retries: int = 3
    ) -> dict:
        """
        コードを実行し、結果を返す
        
        Args:
            code: 実行するPythonコード
            max_retries: エラー時の最大再試行回数
            
        Returns:
            {
                "success": bool,
                "answer": str,
                "figure": plotly.graph_objs.Figure or None,
                "data": pd.DataFrame or None,
                "error": str or None
            }
        """
        pass
    
    @staticmethod
    def save_outputs(
        session_id: str,
        figure: object,
        data: object,
        export_formats: list
    ) -> dict:
        """
        グラフとデータを保存
        
        Args:
            session_id: セッションID（例: "20251211_143022_借入返済額検討"）
            figure: Plotlyのfigureオブジェクト
            data: pandasのDataFrame
            export_formats: 保存形式リスト（["HTML", "PNG"]）
            
        Returns:
            {"html_path": str, "png_path": str, "csv_path": str}
        """
        pass
```

#### 4.2.2 modules/financial_analyzer.py
```python
"""
財務データの動的読み込みと会話ログ管理
"""

class DataLoader:
    """財務データの動的読み込み"""
    
    @staticmethod
    def list_available_files() -> dict:
        """
        利用可能なファイル一覧を取得
        
        Returns:
            {
                "pl": ["H27_monthly.csv", ..., "R6_monthly.csv"],
                "bs": ["H27_monthly_bs.csv", ..., "R6_monthly_bs.csv"],
                "masters": ["account_master.csv", "bs_account_master.csv"],
                "uploaded": ["20251211_143022_資金繰表.xlsx", ...]
            }
        """
        pass
    
    @staticmethod
    def get_file_structure_prompt() -> str:
        """
        Geminiに渡すデータ構造説明プロンプトを生成
        
        Returns:
            データ構造の説明文
        """
        pass


class ConversationLogger:
    """会話ログの管理"""
    
    @staticmethod
    def create_session(theme: str = "一般") -> str:
        """
        新しいセッションを作成
        
        Args:
            theme: 会話のテーマ
            
        Returns:
            セッションID（例: "20251211_143022_借入返済額検討"）
        """
        pass
    
    @staticmethod
    def save_message(
        session_id: str,
        role: str,
        content: str,
        code: str = None,
        graph_paths: dict = None
    ):
        """
        メッセージをログに追加
        
        Args:
            session_id: セッションID
            role: "user" or "assistant"
            content: メッセージ内容
            code: 生成されたコード（assistantのみ）
            graph_paths: グラフの保存パス
        """
        pass
    
    @staticmethod
    def export_markdown(session_id: str) -> str:
        """
        会話をMarkdown形式でエクスポート
        
        Args:
            session_id: セッションID
            
        Returns:
            Markdownファイルパス
        """
        pass
```

### 4.3 システムプロンプト設計

#### 4.3.1 基本プロンプト
```python
SYSTEM_PROMPT = """
あなたは林業経営者向けの財務分析AIアシスタントです。
ユーザーの質問に対して、Pythonコードを生成して財務データを分析します。

【データ構造】
1. 損益計算書（PL）データ
   - 場所: data/monthly_pl/{年度}_monthly.csv
   - エンコーディング: Shift-JIS
   - 列: タイトル, 科目コード, 科目名称, 当月迄累計金額, 当月迄累計構成比, 4月, 5月, ..., 3月
   - 年度: H27, H28, ..., R6
   
2. 貸借対照表（BS）データ
   - 場所: data/monthly_bs/{年度}_monthly_bs.csv
   - エンコーディング: Shift-JIS
   - 列: コード, 科目名称, 4月（当月残高）, 5月（当月残高）, ..., 3月（当月残高）
   - 注意: PLは「科目コード」、BSは「コード」列
   
3. 科目マスタ
   - PL: config/account_master.csv（UTF-8）
   - BS: config/bs_account_master.csv（UTF-8）
   - 列: 科目コード, 科目名, 大分類, 中分類, 表示順

【利用可能なファイル】
{available_files}

【アップロードされた参考資料】
{uploaded_files}

【コード生成ルール】
1. 必要なライブラリのみインポートする（pandas, plotly, numpy）
2. ファイル読み込み時は必ずエンコーディングを指定する
3. グラフはPlotlyで生成し、変数名は`fig`とする
4. 結果は以下の形式の辞書で返す：
   ```python
   result = {
       "answer": "ユーザーへの回答文（Markdown形式）",
       "fig": fig,  # Plotlyのfigure（ない場合はNone）
       "data": df   # 主要データのDataFrame（ない場合はNone）
   }
   ```
5. エラーハンドリングを必ず実装する
6. コメントは日本語で記述する

【禁止事項】
- ファイルの削除・変更（読み込みのみ許可）
- 外部プロセスの起動
- evalやexecの使用

【実行環境】
- Python 3.9以上
- 利用可能ライブラリ: pandas, plotly, numpy, openpyxl
"""
```

---

## 5. 実装手順

### Phase A: 基盤構築（優先度: 高）

#### A-1. 環境準備
- [ ] `requirements.txt`にkaleido追加
- [ ] `.gitignore`に`data/uploaded/`, `notebooks/chat_logs/`追加
- [ ] `data/uploaded/`, `notebooks/chat_logs/`ディレクトリ作成

#### A-2. modules/gemini_chat.py実装
- [ ] `GeminiClient`クラス
  - [ ] `__init__`: APIクライアント初期化
  - [ ] `generate_code`: プロンプト構築 + コード生成
  - [ ] `get_available_models`: モデル一覧取得
- [ ] `CodeExecutor`クラス
  - [ ] `validate_code`: 禁止操作チェック
  - [ ] `execute_code`: サンドボックス実行 + エラー再試行
  - [ ] `save_outputs`: グラフ・データ保存

#### A-3. modules/financial_analyzer.py実装
- [ ] `DataLoader`クラス
  - [ ] `list_available_files`: ファイル一覧取得
  - [ ] `get_file_structure_prompt`: プロンプト生成
- [ ] `ConversationLogger`クラス
  - [ ] `create_session`: セッション作成
  - [ ] `save_message`: メッセージ保存
  - [ ] `export_markdown`: Markdown出力

### Phase B: UI実装（優先度: 高）

#### B-1. 既存タブの移行
- [ ] `pages/1_📊_PL分析.py`作成（app.pyからPLタブのコードをコピー）
- [ ] `pages/2_💰_BS分析.py`作成（app.pyからBSタブのコードをコピー）
- [ ] 動作確認（既存機能が正常に動作するか）
- [ ] `app.py`削除またはトップページ化

#### B-2. pages/3_💬_AIチャット.py実装
- [ ] 基本レイアウト構築
  - [ ] サイドバー: モデル選択、参考資料アップロード
  - [ ] メインエリア: チャット履歴表示、入力欄
- [ ] チャット機能実装
  - [ ] ユーザー入力 → Geminiコード生成
  - [ ] コード承認UI（expander + 実行/キャンセルボタン）
  - [ ] コード実行 → 結果表示
- [ ] セッション管理（`st.session_state`）
  - [ ] 会話履歴保持
  - [ ] モデル選択状態保持
  - [ ] アップロードファイル管理

### Phase C: 拡張機能（優先度: 中）

#### C-1. 参考資料アップロード
- [ ] ファイルアップロード処理
- [ ] `data/uploaded/`への保存（タイムスタンプ付きファイル名）
- [ ] Geminiプロンプトへのファイルパス追加

#### C-2. グラフ保存機能
- [ ] Plotly → HTML保存
- [ ] Plotly → PNG保存（kaleido使用）
- [ ] 保存形式選択UI（マルチセレクト）

#### C-3. 会話ログ保存
- [ ] 「💾 会話を保存」ボタン実装
- [ ] Markdown形式でのエクスポート
- [ ] グラフ・データの同時保存

### Phase D: テスト・ドキュメント（優先度: 中）

#### D-1. 単体テスト
- [ ] `modules/gemini_chat.py`のテスト
- [ ] `modules/financial_analyzer.py`のテスト
- [ ] エラーハンドリングのテスト

#### D-2. 統合テスト
- [ ] 簡単な質問（「R6の売上高を教えて」）
- [ ] 複雑な質問（「R6とR5の借入返済額を比較して」）
- [ ] エラーケース（存在しない年度、科目コード）

#### D-3. ドキュメント更新
- [ ] `README.md`にAIチャット機能の説明追加
- [ ] `CLAUDE.md`に実装詳細追加
- [ ] 使い方ガイド（スクリーンショット付き）

---

## 6. テストシナリオ

### 6.1 基本機能テスト

| No | テストケース | 期待結果 |
|----|------------|---------|
| 1 | R6の売上高を教えて | 売上高データ表示 + 月次推移グラフ |
| 2 | R6とR5の借入返済額を比較して | 2年分のデータ + 比較グラフ |
| 3 | 過去5年間の役員報酬推移をグラフ化して | 5年分の折れ線グラフ |
| 4 | 存在しない年度（R10）を指定 | エラーメッセージ + 利用可能年度の提示 |
| 5 | 存在しない科目コード（999）を指定 | エラーメッセージ + 科目マスタ参照の提案 |

### 6.2 エラーハンドリングテスト

| No | エラー種別 | 期待動作 |
|----|----------|---------|
| 1 | KeyError（存在しない列名） | 自動再生成（最大3回） |
| 2 | FileNotFoundError | エラーメッセージ + ファイル一覧表示 |
| 3 | UnicodeDecodeError | エンコーディング指定の修正コード生成 |
| 4 | SyntaxError | エラー表示 + ユーザーに質問の言い換えを促す |

### 6.3 セキュリティテスト

| No | テストケース | 期待結果 |
|----|------------|---------|
| 1 | `os.remove`を含むコード生成 | validate_codeでブロック + エラー表示 |
| 2 | `subprocess`を含むコード生成 | validate_codeでブロック + エラー表示 |
| 3 | notebooks/chat_logs/外への書き込み | validate_codeでブロック + エラー表示 |

---

## 7. 依存関係

### 7.1 追加ライブラリ

`requirements.txt`に以下を追加：

```
# 既存ライブラリ（変更なし）
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.17.0
openpyxl>=3.1.0
xlsxwriter>=3.1.0
japanize-matplotlib>=1.1.3
python-dotenv>=1.0.0

# 新規追加
google-generativeai>=0.3.0  # Gemini API
kaleido>=0.2.1              # Plotly PNG出力
```

### 7.2 環境変数

`.env`ファイル（既に作成済み）:
```
GEMINI_API_KEY=your_api_key_here
```

---

## 8. リスクと対策

| リスク | 影響度 | 対策 |
|-------|-------|-----|
| Gemini API rate limit超過 | 高 | リトライ処理 + ユーザーへの通知 |
| 生成コードの実行エラー | 中 | 自動再試行（最大3回） + エラーログ保存 |
| 大量データ読み込みによるメモリ不足 | 中 | 動的読み込み + 必要なデータのみ読み込み |
| セキュリティリスク（危険なコード生成） | 高 | validate_codeでの厳格なチェック |

---

## 9. 将来的な拡張案（Phase 3以降）

- [ ] 音声入力対応（Whisper API連携）
- [ ] マルチモーダル入力（グラフ画像をアップロード → 分析）
- [ ] 過去の会話履歴検索機能
- [ ] AIによる自動レポート生成（週次/月次）
- [ ] アラート機能（特定指標が閾値を超えた場合に通知）

---

## 10. 参考資料

- Gemini API公式ドキュメント: https://ai.google.dev/gemini-api/docs
- Streamlit公式ドキュメント: https://docs.streamlit.io
- Plotly公式ドキュメント: https://plotly.com/python/

---

**承認**: Claude Code  
**最終更新**: 2025-12-11
