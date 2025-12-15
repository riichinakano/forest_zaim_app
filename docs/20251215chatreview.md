# 林業財務分析アプリ - AIチャット機能改善 要件定義書

**作成日**: 2025-12-14  
**バージョン**: 1.3.0  
**対象**: AIチャット機能のレスポンス速度改善とモデル選択機能追加

---

## 1. 概要

### 1.1 目的
現在のAIチャット機能のレスポンス速度を改善し、ユーザー体験を向上させる。

### 1.2 現状の課題
- 質問ごとにCSVデータを読み込むため、レスポンスが遅い（10-15秒）
- 単純な質問でもコード生成が発生し、時間がかかる
- モデル選択ができず、用途に応じた使い分けができない

### 1.3 目標
- **単純な質問**: 10秒 → **3秒以内**
- **複雑な質問**: 15秒 → **20秒以内**（実質的には維持、エラー率低下で体感速度向上）
- ユーザーがFlash/Proを選択可能に

---

## 2. 実装機能の詳細

### 2.1 フェーズ1: 優先度高（即実装）

#### 機能1-1: データキャッシュ最適化

**目的**: データ読み込み時間の削減

**実装内容**:

1. **キャッシュTTLの変更**
   - 対象ファイル: `modules/data_loader.py`
   - 変更箇所: 
     ```python
     # 変更前
     @st.cache_data(ttl=3600)
     def load_all_data(data_dir: str = "data/monthly_pl") -> pd.DataFrame:
     
     @st.cache_data(ttl=3600)
     def load_all_bs_data(data_dir: str = "data/monthly_bs") -> pd.DataFrame:
     
     # 変更後
     @st.cache_data(ttl=None)  # アプリ起動中ずっと保持
     def load_all_data(data_dir: str = "data/monthly_pl") -> pd.DataFrame:
     
     @st.cache_data(ttl=None)
     def load_all_bs_data(data_dir: str = "data/monthly_bs") -> pd.DataFrame:
     ```

2. **起動時の全データ読み込み**
   - 対象ファイル: `pages/3_💬_AIチャット.py`
   - 追加箇所: ページ読み込み直後（セッションステートの初期化部分）
   - 実装内容:
     ```python
     # セッション開始時に全データをロード
     if 'financial_data_loaded' not in st.session_state:
         with st.spinner('財務データを読み込み中...'):
             st.session_state.pl_data = load_all_data('data/monthly_pl')
             st.session_state.bs_data = load_all_bs_data('data/monthly_bs')
             st.session_state.pl_master = load_master_cached('config')
             st.session_state.bs_master = load_bs_master_cached('config')
             st.session_state.financial_data_loaded = True
     ```

3. **システムプロンプトの更新**
   - 対象ファイル: `modules/gemini_chat.py`
   - 変更箇所: `_build_system_prompt`メソッド
   - 追加内容:
     ```python
     """
     【データアクセス方法】
     データは起動時に読み込み済みです。以下の関数を使用してください:
     
     from modules.data_loader import load_all_data, load_all_bs_data
     df_pl = load_all_data('data/monthly_pl')  # 全PL年度（キャッシュから高速取得）
     df_bs = load_all_bs_data('data/monthly_bs')  # 全BS年度（キャッシュから高速取得）
     
     CSVファイルを直接pd.read_csv()で読み込まないでください。
     """
     ```

**期待効果**: データアクセス時間 数秒 → 0.1秒未満

---

#### 機能1-2: モデル選択機能

**目的**: 用途に応じたモデル使い分け

**実装内容**:

1. **利用可能モデルの追加**
   - 対象ファイル: `modules/gemini_chat.py`
   - 変更箇所: `AVAILABLE_MODELS`
   ```python
   # 変更前
   AVAILABLE_MODELS = {
       "Gemini 2.5 Flash（推奨）★": "gemini-2.5-flash"
   }
   
   # 変更後
   AVAILABLE_MODELS = {
       "Gemini 2.5 Flash（高速・推奨）★": "gemini-2.5-flash",
       "Gemini 2.5 Pro（高精度・複雑な分析）": "gemini-2.5-pro"
   }
   ```

2. **UI実装: モデル選択ドロップダウン**
   - 対象ファイル: `pages/3_💬_AIチャット.py`
   - 配置場所: サイドバー「1. 基本設定」セクション内
   - 実装内容:
     ```python
     # サイドバー「1. 基本設定」内に追加
     st.sidebar.subheader("1. 基本設定")
     
     # セッション管理（既存）
     # ...
     
     # モデル選択（新規追加）
     selected_model_display = st.sidebar.selectbox(
         "🤖 使用モデル",
         options=list(GeminiClient.AVAILABLE_MODELS.keys()),
         index=0,  # デフォルトはFlash
         help="Flash: 高速、Pro: 高精度"
     )
     selected_model = GeminiClient.AVAILABLE_MODELS[selected_model_display]
     
     # セッションステートに保存（次の質問でも維持）
     if 'selected_model' not in st.session_state:
         st.session_state.selected_model = selected_model
     else:
         st.session_state.selected_model = selected_model
     ```

3. **トークン数カウントとコスト表示**
   - 対象ファイル: `pages/3_💬_AIチャット.py`
   - 配置場所: サイドバー下部
   - 実装内容:
     ```python
     # セッショントークン数の初期化
     if 'total_tokens' not in st.session_state:
         st.session_state.total_tokens = 0
     
     # サイドバー下部に表示
     st.sidebar.markdown("---")
     st.sidebar.metric(
         "今セッションの使用量",
         value=f"{st.session_state.total_tokens:,} tokens",
         help="APIリクエストで使用したトークン数"
     )
     ```

4. **トークン数の記録**
   - 対象ファイル: `modules/gemini_chat.py`
   - 変更箇所: `generate_code`メソッド
   - 実装内容: レスポンスから`usage_metadata`を取得してトークン数を返す
     ```python
     def generate_code(self, ...) -> Tuple[str, int]:
         """
         Returns:
             (生成されたコード, 使用トークン数)
         """
         response = self.model.generate_content(full_prompt)
         
         # トークン数を取得
         tokens = response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
         
         code = self._extract_code_from_response(response.text)
         return code, tokens
     ```

**期待効果**: ユーザーが用途に応じてモデルを選択可能

---

#### 機能1-3: UI/UX改善（進捗表示）

**目的**: 処理中の待ち時間を体感的に短くする

**実装内容**:

1. **段階的な進捗表示**
   - 対象ファイル: `pages/3_💬_AIチャット.py`
   - 変更箇所: コード生成・実行部分
   - 実装内容:
     ```python
     # コード生成
     with st.status("処理中...", expanded=True) as status:
         status.update(label="コード生成中...", state="running")
         code, tokens = gemini_client.generate_code(...)
         
         status.update(label="コード検証中...", state="running")
         is_safe, error_msg = CodeExecutor.validate_code(code)
         
         if is_safe:
             status.update(label="実行中...", state="running")
             result = CodeExecutor.execute_code(code)
             
             if result["figure"]:
                 status.update(label="グラフ作成中...", state="running")
                 # グラフ保存処理
             
             status.update(label="完了", state="complete")
     ```

**期待効果**: 体感速度の向上（実時間は変わらないが、待ち時間が苦痛でなくなる）

---

### 2.2 フェーズ2: 優先度中（テスト後に実装）

#### 機能2-1: 質問タイプ分類（テキスト返答機能）

**目的**: データ参照不要な質問への高速応答

**実装内容**:

1. **質問分類関数の追加**
   - 対象ファイル: `modules/gemini_chat.py`
   - 新規メソッド: `classify_question_type`
   ```python
   @staticmethod
   def classify_question_type(user_question: str) -> str:
       """
       質問を分類
       Returns: "text_only" or "code_execution"
       """
       # テキスト返答で十分なキーワード
       text_only_keywords = [
           "とは", "とは何", "教えて", "説明して", "意味",
           "計算式", "どういう", "違い", "何が違う",
           "おすすめ", "アドバイス", "考え方"
       ]
       
       # コード実行が必要なキーワード
       code_keywords = [
           "R6", "R5", "R4", "R3", "R2", "R1",  # 年度
           "H27", "H28", "H29", "H30",  # 年度
           "推移", "グラフ", "比較", "合計", "平均",
           "円グラフ", "棒グラフ", "折れ線", "表示",
           "データ", "いくら", "何円"
       ]
       
       # コード実行キーワードが含まれる場合
       if any(kw in user_question for kw in code_keywords):
           return "code_execution"
       
       # テキスト返答キーワードが含まれる場合
       if any(kw in user_question for kw in text_only_keywords):
           return "text_only"
       
       # 判定できない場合は安全側に倒す
       return "code_execution"
   ```

2. **テキスト専用レスポンス生成**
   - 対象ファイル: `modules/gemini_chat.py`
   - 新規メソッド: `generate_text_response`
   ```python
   def generate_text_response(self, user_question: str, conversation_history: Optional[List] = None) -> Tuple[str, int]:
       """
       データ参照不要な質問へのテキスト返答
       Returns:
           (回答テキスト, 使用トークン数)
       """
       prompt = f"""
あなたは林業経営者向けの財務アドバイザーです。
以下の質問に、簡潔に回答してください（データ参照は不要です）。

【財務知識】
- 売上総利益 = 売上高 - 売上原価
- 営業利益 = 売上総利益 - 販売費及び一般管理費
- 経常利益 = 営業利益 + 営業外収益 - 営業外費用
- 当期純利益 = 経常利益 - 特別損失
- 流動比率 = 流動資産 / 流動負債 × 100
- 自己資本比率 = 純資産 / 総資産 × 100

質問: {user_question}

回答（300字以内、Markdown形式）:
"""
       
       response = self.model.generate_content(prompt)
       tokens = response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
       
       return response.text, tokens
   ```

3. **分岐処理の実装**
   - 対象ファイル: `pages/3_💬_AIチャット.py`
   - 変更箇所: 質問送信時の処理
   ```python
   if user_question:
       # 質問タイプを分類
       question_type = GeminiClient.classify_question_type(user_question)
       
       if question_type == "text_only":
           # テキスト返答モード
           with st.status("回答生成中...", expanded=True) as status:
               answer, tokens = gemini_client.generate_text_response(user_question, ...)
               st.session_state.total_tokens += tokens
               status.update(label="完了", state="complete")
           
           # 回答を表示
           st.markdown(answer)
           
           # モード切替ボタン（誤分類時の対応）
           if st.button("🔄 データ参照モードで再実行"):
               # コード生成・実行に切り替え
               ...
       
       else:
           # コード実行モード（既存処理）
           ...
   ```

**期待効果**: テキスト返答質問 10秒 → 1-2秒

---

#### 機能2-2: エラーハンドリング（モード切替）

**目的**: 誤分類時のユーザー救済

**実装内容**:

- テキスト返答後に「🔄 データ参照モードで再実行」ボタンを表示
- ボタンクリックで強制的にコード生成・実行モードに切り替え
- セッションステートに`force_code_execution=True`フラグを設定

---

### 2.3 フェーズ3: 今回は実装しない（将来検討）

#### 機能3-1: 事前計算キャッシュ
- よくある質問の答えを事前計算して即答

#### 機能3-2: システムプロンプトの高度化
- 科目コードの詳細リスト、よくあるエラーパターンを追記

---

## 3. ログ・分析機能

### 3.1 会話ログへの記録項目追加

**対象ファイル**: `modules/financial_analyzer.py`

**追加項目**:
- 使用モデル名
- 質問タイプ（text_only / code_execution）
- 処理時間（秒）
- 使用トークン数
- エラー有無

**実装内容**:
```python
# ConversationLogger.save_message の引数追加
@staticmethod
def save_message(
    session_id: str,
    role: str,
    content: str,
    code: Optional[str] = None,
    graph_paths: Optional[Dict[str, str]] = None,
    # ↓ 以下を追加
    model_name: Optional[str] = None,
    question_type: Optional[str] = None,
    processing_time: Optional[float] = None,
    tokens_used: Optional[int] = None,
    has_error: bool = False
):
    """
    メッセージをログに追加
    """
    message = {
        "timestamp": datetime.now().isoformat(),
        "role": role,
        "content": content,
        "model_name": model_name,  # 追加
        "question_type": question_type,  # 追加
        "processing_time": processing_time,  # 追加
        "tokens_used": tokens_used,  # 追加
        "has_error": has_error  # 追加
    }
    # ...
```

---

## 4. テスト計画

### 4.1 テスト用質問リスト

| No | 質問内容 | 期待動作 | 目標時間 |
|----|---------|---------|---------|
| 1 | 「R6の売上高を教えて」 | コード実行 | 3秒以内 |
| 2 | 「過去5年の営業利益推移をグラフ化」 | コード実行 | 20秒以内 |
| 3 | 「営業利益とは何ですか？」 | テキスト返答（Phase2） | 2秒以内 |
| 4 | 「流動比率の計算式を教えて」 | テキスト返答（Phase2） | 2秒以内 |
| 5 | 「R6とR5の借入金を比較して」 | コード実行 | 20秒以内 |

### 4.2 成功基準

**フェーズ1完了時**:
- データ読み込み: 初回のみ、2回目以降0.1秒未満
- モデル選択: Flash/Pro切替可能
- トークン数表示: 正常に動作
- 進捗表示: 各ステップが表示される

**フェーズ2完了時**:
- テキスト返答質問: 2秒以内
- コード実行質問: 3-20秒（データアクセス高速化の効果）

### 4.3 テスト手順

1. アプリを再起動
2. AIチャットページを開く → データ読み込み表示を確認
3. 上記5つの質問を順次実行
4. 処理時間・結果の正確性を記録
5. モデルをProに切り替えて同じ質問を実行
6. トークン数の増加を確認

---

## 5. 実装ファイル一覧

### 5.1 変更ファイル

| ファイル | 変更内容 | フェーズ |
|---------|---------|---------|
| `modules/data_loader.py` | キャッシュTTL変更 | Phase1 |
| `modules/gemini_chat.py` | モデル追加、分類関数追加、トークン数返却 | Phase1, 2 |
| `pages/3_💬_AIチャット.py` | 起動時データ読み込み、モデル選択UI、進捗表示 | Phase1, 2 |
| `modules/financial_analyzer.py` | ログ記録項目追加 | Phase1 |

### 5.2 新規ファイル
なし

---

## 6. リスク・制約事項

### 6.1 技術的リスク

| リスク | 影響 | 対策 |
|--------|------|------|
| メモリ使用量増加 | アプリが重くなる | データサイズを監視、必要に応じてキャッシュクリア機能追加 |
| 質問分類の誤判定 | ユーザー体験低下 | モード切替ボタンで救済 |
| Gemini Pro のコスト | 予算超過 | トークン数表示で使用量を可視化 |

### 6.2 制約事項

- Gemini API無料枠: Flash 1,500 RPD (Requests Per Day)、Pro 10 RPD
- セッションステートのメモリ上限: Streamlit Cloudの場合1GB程度
- PL/BSデータサイズ: 合計で推定50MB程度（問題なし）

---

## 7. 今後の拡張案（Phase 3以降）

### 7.1 機能拡張
- RAG（Retrieval-Augmented Generation）による高度な分析
- 自動レポート生成機能
- アラート機能（異常値検知）

### 7.2 パフォーマンス改善
- Parquet形式への変換（データ読み込み高速化）
- SQLiteによるクエリ最適化
- 並列処理によるグラフ生成高速化

---

## 8. 承認・実装スケジュール

### 8.1 承認
- [ ] 要件定義書レビュー
- [ ] 仕様承認

### 8.2 実装スケジュール

**フェーズ1**（優先度高）:
- データキャッシュ最適化: 30分
- モデル選択機能: 1時間
- UI/UX改善（進捗表示）: 30分
- 合計: **2時間**

**テスト**: 30分

**フェーズ2**（優先度中）:
- 質問タイプ分類: 1.5時間
- エラーハンドリング: 30分
- 合計: **2時間**

**テスト**: 30分

**総実装時間**: 約5時間

---

## 9. 補足資料

### 9.1 参考ドキュメント
- `docs/gemini_models.md` - Geminiモデル仕様
- `README.md` - 既存機能仕様

### 9.2 関連Issue
- （GitHubに作成予定）

---
