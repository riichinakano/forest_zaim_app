"""
財務データの動的読み込みと会話ログ管理

このモジュールは以下の機能を提供します:
- 利用可能な財務データファイルの一覧取得
- データ構造説明プロンプトの生成
- 会話ログのセッション管理
- Markdown形式での会話ログエクスポート
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class DataLoader:
    """財務データの動的読み込み"""

    @staticmethod
    def list_available_files() -> Dict[str, List[str]]:
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
        files = {
            "pl": [],
            "bs": [],
            "masters": [],
            "uploaded": []
        }

        # PLデータ
        pl_dir = Path("data/monthly_pl")
        if pl_dir.exists():
            files["pl"] = sorted([
                f.name for f in pl_dir.glob("*_monthly.csv")
            ])

        # BSデータ
        bs_dir = Path("data/monthly_bs")
        if bs_dir.exists():
            files["bs"] = sorted([
                f.name for f in bs_dir.glob("*_monthly_bs.csv")
            ])

        # 科目マスタ
        masters_dir = Path("config")
        if masters_dir.exists():
            files["masters"] = [
                "account_master.csv",
                "bs_account_master.csv"
            ]

        # アップロードされたファイル
        uploaded_dir = Path("data/uploaded")
        if uploaded_dir.exists():
            files["uploaded"] = sorted([
                f.name for f in uploaded_dir.iterdir() if f.is_file()
            ])

        return files

    @staticmethod
    def get_file_structure_prompt() -> str:
        """
        Geminiに渡すデータ構造説明プロンプトを生成

        Returns:
            データ構造の説明文
        """
        files = DataLoader.list_available_files()

        prompt = f"""
【利用可能なデータファイル】

1. 損益計算書（PL）データ
   利用可能な年度: {', '.join(files['pl'])}
   ファイルパス: data/monthly_pl/{{年度}}_monthly.csv
   エンコーディング: Shift-JIS

2. 貸借対照表（BS）データ
   利用可能な年度: {', '.join(files['bs'])}
   ファイルパス: data/monthly_bs/{{年度}}_monthly_bs.csv
   エンコーディング: Shift-JIS

3. 科目マスタ
   - PL科目マスタ: config/account_master.csv（UTF-8）
   - BS科目マスタ: config/bs_account_master.csv（UTF-8）

4. アップロードされた参考資料
   {', '.join(files['uploaded']) if files['uploaded'] else 'なし'}
"""
        return prompt


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
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # テーマから使用できない文字を除去
        safe_theme = "".join(c for c in theme if c.isalnum() or c in "ー_")
        session_id = f"{timestamp}_{safe_theme}"

        # セッションディレクトリの作成
        session_dir = Path(f"notebooks/chat_logs/{session_id}")
        session_dir.mkdir(parents=True, exist_ok=True)

        return session_id

    @staticmethod
    def save_message(
        session_id: str,
        role: str,
        content: str,
        code: Optional[str] = None,
        graph_paths: Optional[Dict[str, str]] = None,
        model_name: Optional[str] = None,
        question_type: Optional[str] = None,
        processing_time: Optional[float] = None,
        tokens_used: Optional[int] = None,
        has_error: bool = False
    ):
        """
        メッセージをログに追加

        Args:
            session_id: セッションID
            role: "user" or "assistant"
            content: メッセージ内容
            code: 生成されたコード（assistantのみ）
            graph_paths: グラフの保存パス
            model_name: 使用したモデル名
            question_type: 質問タイプ（text_only / code_execution）
            processing_time: 処理時間（秒）
            tokens_used: 使用トークン数
            has_error: エラー有無
        """
        # セッションディレクトリの確認
        session_dir = Path(f"notebooks/chat_logs/{session_id}")
        if not session_dir.exists():
            session_dir.mkdir(parents=True, exist_ok=True)

        # ログファイルのパス
        log_file = session_dir / "conversation.jsonl"

        # メッセージの構築
        import json
        message = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "model_name": model_name,
            "question_type": question_type,
            "processing_time": processing_time,
            "tokens_used": tokens_used,
            "has_error": has_error
        }

        if code:
            message["code"] = code

        if graph_paths:
            message["graph_paths"] = graph_paths

        # JSONL形式で追記
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(message, ensure_ascii=False) + "\n")

    @staticmethod
    def export_markdown(session_id: str, model_name: str = "Gemini 2.5 Flash") -> str:
        """
        会話をMarkdown形式でエクスポート

        Args:
            session_id: セッションID
            model_name: 使用したモデル名

        Returns:
            Markdownファイルパス
        """
        # セッションディレクトリの確認
        session_dir = Path(f"notebooks/chat_logs/{session_id}")
        if not session_dir.exists():
            return ""

        # ログファイルの読み込み
        log_file = session_dir / "conversation.jsonl"
        if not log_file.exists():
            return ""

        import json
        messages = []
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                messages.append(json.loads(line))

        # Markdown形式で出力
        md_file = session_dir / "conversation.md"

        # セッションのテーマを抽出（session_idから）
        theme = session_id.split("_", 2)[-1] if "_" in session_id else "一般"
        timestamp_str = messages[0]["timestamp"][:19] if messages else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(md_file, "w", encoding="utf-8") as f:
            # ヘッダー
            f.write(f"# {theme}\n\n")
            f.write(f"**日時**: {timestamp_str}  \n")
            f.write(f"**モデル**: {model_name}\n\n")
            f.write("---\n\n")

            # メッセージ
            for i, msg in enumerate(messages):
                role = "ユーザー" if msg["role"] == "user" else "アシスタント"
                f.write(f"## {role}\n\n")
                f.write(f"{msg['content']}\n\n")

                # コードがある場合
                if "code" in msg:
                    f.write("### 生成されたコード\n\n")
                    f.write("```python\n")
                    f.write(msg["code"])
                    f.write("\n```\n\n")

                # グラフがある場合
                if "graph_paths" in msg:
                    for path_type, path in msg["graph_paths"].items():
                        if path_type == "png_path":
                            # 相対パスに変換
                            relative_path = Path(path).name
                            f.write(f"![グラフ]({relative_path})\n\n")

        return str(md_file)

    @staticmethod
    def get_conversation_history(session_id: str) -> List[Dict[str, str]]:
        """
        セッションの会話履歴を取得

        Args:
            session_id: セッションID

        Returns:
            会話履歴のリスト
        """
        # セッションディレクトリの確認
        session_dir = Path(f"notebooks/chat_logs/{session_id}")
        if not session_dir.exists():
            return []

        # ログファイルの読み込み
        log_file = session_dir / "conversation.jsonl"
        if not log_file.exists():
            return []

        import json
        messages = []
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                msg = json.loads(line)
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        return messages
