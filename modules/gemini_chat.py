"""
Gemini API連携とコード生成・実行を管理

このモジュールは以下の機能を提供します:
- Gemini APIを使用したコード生成
- 生成されたコードの安全性検証
- サンドボックス環境でのコード実行
- グラフ・データの保存
"""

import os
import re
from typing import Optional, Dict, List, Tuple, Any
import google.generativeai as genai
import pandas as pd
import plotly.graph_objs as go
from pathlib import Path


class GeminiClient:
    """Gemini APIクライアント"""

    # 利用可能なモデル一覧（無料枠で使用可能なモデルのみ）
    AVAILABLE_MODELS = {
        "Gemini 2.5 Flash（推奨）★": "gemini-2.5-flash"
    }

    def __init__(self, model_name: str, api_key: str):
        """
        Args:
            model_name: Geminiモデル名（例: "gemini-2.5-flash"）
            api_key: Gemini APIキー
        """
        self.model_name = model_name
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate_code(
        self,
        user_question: str,
        available_files: Dict[str, List[str]],
        uploaded_files: Optional[List[str]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
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
        # システムプロンプトの構築
        system_prompt = self._build_system_prompt(available_files, uploaded_files)

        # 会話履歴を含むプロンプトの構築
        full_prompt = system_prompt + "\n\n"

        if conversation_history:
            full_prompt += "【これまでの会話】\n"
            for message in conversation_history[-5:]:  # 直近5件のみ
                role = "ユーザー" if message["role"] == "user" else "アシスタント"
                full_prompt += f"{role}: {message['content']}\n"
            full_prompt += "\n"

        full_prompt += f"【新しい質問】\n{user_question}\n\n"
        full_prompt += "上記の質問に答えるためのPythonコードを生成してください。コードのみを出力してください（説明文は不要）。"

        # コード生成
        response = self.model.generate_content(full_prompt)

        # コードを抽出（```python ... ``` の部分を取り出す）
        code = self._extract_code_from_response(response.text)

        return code

    def _build_system_prompt(
        self,
        available_files: Dict[str, List[str]],
        uploaded_files: Optional[List[str]]
    ) -> str:
        """システムプロンプトを構築"""

        # ファイル一覧を整形
        files_str = "【利用可能なファイル】\n"
        files_str += f"PL（損益計算書）データ: {', '.join(available_files.get('pl', []))}\n"
        files_str += f"BS（貸借対照表）データ: {', '.join(available_files.get('bs', []))}\n"
        files_str += f"科目マスタ: {', '.join(available_files.get('masters', []))}\n"

        if uploaded_files:
            files_str += f"\nアップロードされた参考資料:\n"
            for file in uploaded_files:
                files_str += f"  - {file}\n"

        prompt = f"""あなたは林業経営者向けの財務分析AIアシスタントです。
ユーザーの質問に対して、Pythonコードを生成して財務データを分析します。

【データ構造】
1. 損益計算書（PL）データ
   - 場所: data/monthly_pl/{{年度}}_monthly.csv
   - エンコーディング: Shift-JIS
   - 列: タイトル, 科目コード, 科目名称, 当月迄累計金額, 当月迄累計構成比, 4月, 5月, ..., 3月
   - 年度: H27, H28, H29, H30, R1, R2, R3, R4, R5, R6（平成27年～令和6年）
   - 重要: 月次列（4月～3月）の値は「累計金額」ではなく「当月金額」
   - 年間合計の計算: df['年間合計'] = df[['4月', '5月', ..., '3月']].sum(axis=1)

2. 損益計算書の主要科目と計算方法
   - 売上高: 科目コード 410番台（科目マスタの大分類「収益」、中分類「売上」）
   - 売上原価: 科目コード 500番台（大分類「費用」、中分類「製造原価」）
   - 売上総利益 = 売上高 - 売上原価
   - 販売費及び一般管理費: 科目コード 600番台（大分類「費用」、中分類「販管費」）
   - 営業利益 = 売上総利益 - 販管費
   - 営業外収益: 科目コード 700番台（大分類「収益」、中分類「営業外収益」）
   - 営業外費用: 科目コード 800番台（大分類「費用」、中分類「営業外費用」）
   - 経常利益 = 営業利益 + 営業外収益 - 営業外費用
   - 特別損失: 科目コード 900番台（大分類「費用」、中分類「特別損失」）
   - 当期純利益 = 経常利益 - 特別損失

3. 貸借対照表（BS）データ
   - 場所: data/monthly_bs/{{年度}}_monthly_bs.csv
   - エンコーディング: Shift-JIS
   - 列: コード, 科目名称, 4月（当月残高）, 5月（当月残高）, ..., 3月（当月残高）
   - 注意: PLは「科目コード」列、BSは「コード」列

4. 科目マスタ
   - PL: config/account_master.csv（UTF-8）
   - BS: config/bs_account_master.csv（UTF-8）
   - 列: 科目コード, 科目名, 大分類, 中分類, 表示順

{files_str}

【データ読み込みと集計の例】
```python
# 年度データの読み込み
df = pd.read_csv('data/monthly_pl/R6_monthly.csv', encoding='shift-jis')

# 科目マスタの読み込み
master = pd.read_csv('config/account_master.csv', encoding='utf-8')

# 年間合計の計算
months = ['4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月', '1月', '2月', '3月']
df['年間合計'] = df[months].sum(axis=1)

# 中分類ごとの集計（例: 売上高）
df_merged = df.merge(master, on='科目コード', how='left')
sales = df_merged[df_merged['中分類'] == '売上']['年間合計'].sum()

# 売上総利益の計算
revenue = df_merged[df_merged['大分類'] == '収益']['年間合計'].sum()
cost = df_merged[df_merged['中分類'] == '製造原価']['年間合計'].sum()
gross_profit = revenue - cost
```

【コード生成ルール】
1. 必要なライブラリのみインポートする（pandas, plotly, numpy, tabulate）
2. ファイル読み込み時は必ずエンコーディングを指定する
3. グラフはPlotlyで生成し、変数名は`fig`とする
4. 円グラフはplotly.graph_objects.Pieを使用する（例: go.Figure(data=[go.Pie(labels=..., values=...)])）
5. 結果は以下の形式の辞書で返す：
   ```python
   result = {{
       "answer": "ユーザーへの回答文（Markdown形式）",
       "fig": fig,  # Plotlyのfigure（ない場合はNone）
       "data": df   # 主要データのDataFrame（ない場合はNone）
   }}
   ```
6. エラーハンドリングを必ず実装する
7. コメントは日本語で記述する
8. 最後に必ず`result`変数を定義して終了する

【禁止事項】
- ファイルの削除・変更（読み込みのみ許可）
- 外部プロセスの起動
- evalやexecの使用（このコード自体の実行は除く）

【実行環境】
- Python 3.9以上
- 利用可能ライブラリ: pandas, plotly (px, go), numpy, tabulate, openpyxl
"""
        return prompt

    def _extract_code_from_response(self, response_text: str) -> str:
        """レスポンスからPythonコードを抽出"""
        # ```python ... ``` の部分を抽出
        pattern = r'```python\n(.*?)\n```'
        matches = re.findall(pattern, response_text, re.DOTALL)

        if matches:
            return matches[0]

        # ```のみの場合
        pattern = r'```\n(.*?)\n```'
        matches = re.findall(pattern, response_text, re.DOTALL)

        if matches:
            return matches[0]

        # マークダウンがない場合はそのまま返す
        return response_text.strip()

    @staticmethod
    def get_available_models() -> Dict[str, str]:
        """利用可能なモデル一覧を取得"""
        return GeminiClient.AVAILABLE_MODELS


class CodeExecutor:
    """生成されたコードの検証・実行"""

    # 禁止操作のリスト
    BLOCKED_OPERATIONS = [
        'os.remove',
        'os.rmdir',
        'os.unlink',
        'shutil.rmtree',
        'subprocess',
        'eval(',
        '__import__',
        'open(',  # 書き込みモードでのopen
        'compile(',
        'exec(',  # 自身以外の実行
    ]

    # 許可される書き込み先ディレクトリ
    ALLOWED_WRITE_DIRS = [
        'notebooks/chat_logs/',
        'data/uploaded/',
    ]

    @staticmethod
    def validate_code(code: str) -> Tuple[bool, str]:
        """
        コードの安全性をチェック

        Args:
            code: 検証するPythonコード

        Returns:
            (検証結果, エラーメッセージ)
        """
        # 禁止操作のチェック
        for blocked_op in CodeExecutor.BLOCKED_OPERATIONS:
            if blocked_op in code:
                # open()の場合は書き込みモード（'w', 'a'）をチェック
                if blocked_op == 'open(':
                    # 書き込みモードのopen()を検出
                    if re.search(r"open\([^)]*['\"]w['\"]", code) or re.search(r"open\([^)]*['\"]a['\"]", code):
                        # 許可されたディレクトリへの書き込みかチェック
                        allowed = False
                        for allowed_dir in CodeExecutor.ALLOWED_WRITE_DIRS:
                            if allowed_dir in code:
                                allowed = True
                                break

                        if not allowed:
                            return False, f"禁止された操作が含まれています: ファイルへの書き込み（許可されたディレクトリ外）"
                else:
                    return False, f"禁止された操作が含まれています: {blocked_op}"

        # 構文チェック
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            return False, f"構文エラー: {str(e)}"

        return True, ""

    @staticmethod
    def execute_code(
        code: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
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
        # 実行環境の準備
        exec_globals = {
            'pd': pd,
            'go': go,
            'Path': Path,
        }

        # plotlyをインポート
        try:
            import plotly.express as px
            import plotly.graph_objects as go_module
            exec_globals['px'] = px
            exec_globals['go'] = go_module
        except ImportError:
            pass

        # numpyをインポート
        try:
            import numpy as np
            exec_globals['np'] = np
        except ImportError:
            pass

        # tabulateをインポート
        try:
            import tabulate
            exec_globals['tabulate'] = tabulate
        except ImportError:
            pass

        try:
            # コードを実行
            exec(code, exec_globals)

            # 結果を取得
            result = exec_globals.get('result', {})

            if not result:
                return {
                    "success": False,
                    "answer": None,
                    "figure": None,
                    "data": None,
                    "error": "コードが`result`変数を定義していません"
                }

            return {
                "success": True,
                "answer": result.get("answer", ""),
                "figure": result.get("fig", None),
                "data": result.get("data", None),
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "answer": None,
                "figure": None,
                "data": None,
                "error": f"{type(e).__name__}: {str(e)}"
            }

    @staticmethod
    def save_outputs(
        session_id: str,
        figure: Optional[go.Figure],
        data: Optional[pd.DataFrame],
        export_formats: List[str],
        graph_index: int = 1
    ) -> Dict[str, str]:
        """
        グラフとデータを保存

        Args:
            session_id: セッションID（例: "20251211_143022_借入返済額検討"）
            figure: Plotlyのfigureオブジェクト
            data: pandasのDataFrame
            export_formats: 保存形式リスト（["HTML", "PNG"]）
            graph_index: グラフのインデックス番号

        Returns:
            {"html_path": str, "png_path": str, "csv_path": str}
        """
        # セッションディレクトリの作成
        session_dir = Path(f"notebooks/chat_logs/{session_id}")
        session_dir.mkdir(parents=True, exist_ok=True)

        result_paths = {}

        # グラフの保存
        if figure:
            graph_basename = f"graph_{graph_index:02d}"

            # HTML形式で保存
            if "HTML" in export_formats:
                html_path = session_dir / f"{graph_basename}.html"
                figure.write_html(str(html_path))
                result_paths["html_path"] = str(html_path)

            # PNG形式で保存
            if "PNG" in export_formats:
                try:
                    png_path = session_dir / f"{graph_basename}.png"
                    figure.write_image(str(png_path))
                    result_paths["png_path"] = str(png_path)
                except Exception as e:
                    # kaleidoがインストールされていない場合はスキップ
                    result_paths["png_error"] = str(e)

        # データの保存（CSV形式）
        if data is not None:
            csv_path = session_dir / f"data_{graph_index:02d}.csv"
            data.to_csv(str(csv_path), index=False, encoding='utf-8-sig')
            result_paths["csv_path"] = str(csv_path)

        return result_paths
