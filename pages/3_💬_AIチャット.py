"""
林業財務分析アプリケーション - AIチャット

Gemini APIを使用した財務データ分析チャット機能
"""

import streamlit as st
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from modules.gemini_chat import GeminiClient, CodeExecutor
from modules.financial_analyzer import DataLoader, ConversationLogger


# ページ設定
st.set_page_config(
    page_title="AIチャット - 林業財務分析",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)


# 環境変数読み込み
load_dotenv()


def initialize_session_state():
    """セッション状態の初期化"""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "session_id" not in st.session_state:
        st.session_state.session_id = None

    if "uploaded_files_list" not in st.session_state:
        st.session_state.uploaded_files_list = []

    if "graph_counter" not in st.session_state:
        st.session_state.graph_counter = 0

    if "pending_code" not in st.session_state:
        st.session_state.pending_code = None

    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None


def execute_code_and_display(code, question, api_key, selected_model, selected_model_display, export_formats):
    """コードを実行して結果を表示"""
    with st.spinner("コードを実行しています..."):
        result = CodeExecutor.execute_code(code)

        if result["success"]:
            # 回答を表示
            st.markdown(result["answer"])

            # グラフを表示
            if result["figure"]:
                st.plotly_chart(result["figure"], use_container_width=True)

                # グラフを保存
                if export_formats:
                    st.session_state.graph_counter += 1
                    saved_paths = CodeExecutor.save_outputs(
                        session_id=st.session_state.session_id,
                        figure=result["figure"],
                        data=result["data"],
                        export_formats=export_formats,
                        graph_index=st.session_state.graph_counter
                    )

            # データテーブルを表示
            if result["data"] is not None:
                st.dataframe(result["data"], use_container_width=True)

            # メッセージを追加
            assistant_message = {
                "role": "assistant",
                "content": result["answer"],
                "figure": result["figure"],
                "data": result["data"]
            }
            st.session_state.messages.append(assistant_message)

            # ログに保存
            graph_paths = saved_paths if export_formats and result["figure"] else None
            ConversationLogger.save_message(
                st.session_state.session_id,
                role="assistant",
                content=result["answer"],
                code=code,
                graph_paths=graph_paths
            )

            # 保留中のコードをクリア
            st.session_state.pending_code = None
            st.session_state.pending_question = None

        else:
            # エラーメッセージを表示
            st.error(f"❌ 実行エラー: {result['error']}")

            # 自動修正を試みる（最大3回）
            st.markdown("エラーを修正して再実行を試みています...")

            available_files = DataLoader.list_available_files()
            client = GeminiClient(selected_model, api_key)
            conversation_history = ConversationLogger.get_conversation_history(
                st.session_state.session_id
            )

            for attempt in range(3):
                # エラーをフィードバックしてコード再生成
                generated_code = client.generate_code(
                    user_question=f"{question}\n\n【エラー】前回のコードで以下のエラーが発生しました:\n{result['error']}\n\nエラーを修正したコードを生成してください。",
                    available_files=available_files,
                    uploaded_files=st.session_state.uploaded_files_list,
                    conversation_history=conversation_history
                )

                # 再実行
                result = CodeExecutor.execute_code(generated_code)
                if result["success"]:
                    st.success(f"✅ 修正されたコードの実行に成功しました（試行回数: {attempt + 1}）")
                    st.markdown(result["answer"])

                    if result["figure"]:
                        st.plotly_chart(result["figure"], use_container_width=True)

                    if result["data"] is not None:
                        st.dataframe(result["data"], use_container_width=True)

                    # メッセージを追加
                    assistant_message = {
                        "role": "assistant",
                        "content": result["answer"],
                        "figure": result["figure"],
                        "data": result["data"]
                    }
                    st.session_state.messages.append(assistant_message)

                    # ログに保存
                    ConversationLogger.save_message(
                        st.session_state.session_id,
                        role="assistant",
                        content=result["answer"],
                        code=generated_code
                    )

                    # 保留中のコードをクリア
                    st.session_state.pending_code = None
                    st.session_state.pending_question = None
                    break
            else:
                st.error("自動修正に失敗しました。質問を言い換えて再度お試しください。")
                st.session_state.pending_code = None
                st.session_state.pending_question = None


def main():
    """AIチャットのメイン処理"""

    # セッション状態の初期化
    initialize_session_state()

    # タイトル
    st.title("💬 AIチャット - 財務データ分析")
    st.markdown("Gemini APIを活用した自然言語での財務分析")
    st.markdown("---")

    # APIキーの確認
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("⚠️ Gemini APIキーが設定されていません")
        st.info("`.env` ファイルに `GEMINI_API_KEY=your_api_key_here` を設定してください。")
        st.stop()

    # サイドバー
    with st.sidebar:
        st.header("⚙️ 設定")

        # モデル選択
        st.subheader("1. モデル選択")
        models = GeminiClient.get_available_models()
        selected_model_display = st.radio(
            "使用するモデル",
            options=list(models.keys()),
            index=0,
            key="model_select"
        )
        selected_model = models[selected_model_display]

        st.markdown("---")

        # 参考資料アップロード
        st.subheader("2. 参考資料アップロード")
        st.caption("CSV, Excel (.xlsx) 対応")

        uploaded_files = st.file_uploader(
            "ファイルを選択",
            type=["csv", "xlsx"],
            accept_multiple_files=True,
            key="file_uploader"
        )

        # アップロードされたファイルを保存
        if uploaded_files:
            uploaded_dir = Path("data/uploaded")
            uploaded_dir.mkdir(parents=True, exist_ok=True)

            for uploaded_file in uploaded_files:
                # タイムスタンプ付きファイル名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{uploaded_file.name}"
                filepath = uploaded_dir / filename

                # 既に保存済みかチェック
                if str(filepath) not in st.session_state.uploaded_files_list:
                    with open(filepath, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    st.session_state.uploaded_files_list.append(str(filepath))

            st.success(f"✅ {len(uploaded_files)}ファイルをアップロードしました")

        # アップロード済みファイルの表示
        if st.session_state.uploaded_files_list:
            with st.expander("📁 アップロード済みファイル", expanded=False):
                for filepath in st.session_state.uploaded_files_list:
                    st.text(Path(filepath).name)

        st.markdown("---")

        # グラフ保存設定
        st.subheader("3. グラフ保存形式")
        export_formats = st.multiselect(
            "保存形式を選択",
            options=["HTML", "PNG"],
            default=["HTML"],
            key="export_formats"
        )

        st.markdown("---")

        # セッション管理
        st.subheader("4. 会話セッション")

        # 新規セッション開始
        theme_input = st.text_input("セッションのテーマ（任意）", value="一般", key="theme_input")
        if st.button("🆕 新規セッション開始", use_container_width=True):
            session_id = ConversationLogger.create_session(theme_input)
            st.session_state.session_id = session_id
            st.session_state.messages = []
            st.session_state.graph_counter = 0
            st.session_state.pending_code = None
            st.session_state.pending_question = None
            st.success(f"✅ 新規セッション開始: {session_id}")
            st.rerun()

        # 会話保存
        if st.session_state.session_id and st.session_state.messages:
            if st.button("💾 会話を保存", use_container_width=True):
                try:
                    md_path = ConversationLogger.export_markdown(
                        st.session_state.session_id,
                        model_name=selected_model_display
                    )
                    st.success(f"✅ 会話を保存しました")
                    st.caption(f"保存先: {md_path}")
                except Exception as e:
                    st.error(f"保存エラー: {e}")

        st.markdown("---")

        # 情報表示
        if st.session_state.session_id:
            st.caption(f"📝 セッションID: {st.session_state.session_id}")
        st.caption(f"🤖 モデル: {selected_model_display}")
        st.caption(f"💬 メッセージ数: {len(st.session_state.messages)}")

    # メインエリア
    # セッションがない場合は開始を促す
    if not st.session_state.session_id:
        st.info("👈 サイドバーから「🆕 新規セッション開始」をクリックして、会話を始めてください")
        st.stop()

    # 会話履歴の表示
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # グラフがある場合は表示
            if "figure" in message and message["figure"]:
                st.plotly_chart(message["figure"], use_container_width=True)

            # データテーブルがある場合は表示
            if "data" in message and message["data"] is not None:
                st.dataframe(message["data"], use_container_width=True)

    # 保留中のコードがある場合は承認UIを表示
    if st.session_state.pending_code:
        with st.chat_message("assistant"):
            with st.expander("📝 生成されたコード", expanded=True):
                st.code(st.session_state.pending_code, language="python")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("▶️ 実行", type="primary", key="execute_btn"):
                        execute_code_and_display(
                            st.session_state.pending_code,
                            st.session_state.pending_question,
                            api_key,
                            selected_model,
                            selected_model_display,
                            export_formats
                        )
                        st.rerun()
                with col2:
                    if st.button("❌ キャンセル", key="cancel_btn"):
                        st.session_state.pending_code = None
                        st.session_state.pending_question = None
                        st.warning("コードの実行をキャンセルしました")
                        st.rerun()

    # ユーザー入力
    if prompt := st.chat_input("財務データについて質問してください..."):
        # ユーザーメッセージを追加
        st.session_state.messages.append({"role": "user", "content": prompt})

        # ログに保存
        ConversationLogger.save_message(
            st.session_state.session_id,
            role="user",
            content=prompt
        )

        # Gemini APIでコード生成
        with st.spinner("コードを生成しています..."):
            try:
                # 利用可能なファイル一覧を取得
                available_files = DataLoader.list_available_files()

                # Geminiクライアントの初期化
                client = GeminiClient(selected_model, api_key)

                # 会話履歴を取得
                conversation_history = ConversationLogger.get_conversation_history(
                    st.session_state.session_id
                )

                # コード生成
                generated_code = client.generate_code(
                    user_question=prompt,
                    available_files=available_files,
                    uploaded_files=st.session_state.uploaded_files_list,
                    conversation_history=conversation_history
                )

                # コードの安全性チェック
                is_safe, error_message = CodeExecutor.validate_code(generated_code)

                if not is_safe:
                    st.error(f"⚠️ 安全性チェックに失敗しました: {error_message}")
                    st.markdown("コードの再生成を試みています...")

                    # 再生成を試みる（最大3回）
                    for attempt in range(3):
                        generated_code = client.generate_code(
                            user_question=f"{prompt}\n\n【注意】前回のコードで以下のエラーが発生しました: {error_message}\n安全なコードを生成してください。",
                            available_files=available_files,
                            uploaded_files=st.session_state.uploaded_files_list,
                            conversation_history=conversation_history
                        )

                        is_safe, error_message = CodeExecutor.validate_code(generated_code)
                        if is_safe:
                            break

                    if not is_safe:
                        st.error("安全なコードを生成できませんでした。質問を言い換えて再度お試しください。")
                        st.stop()

                # コードを保留状態に設定
                st.session_state.pending_code = generated_code
                st.session_state.pending_question = prompt

                # ページを再読み込みして承認UIを表示
                st.rerun()

            except Exception as e:
                st.error(f"❌ エラーが発生しました: {e}")
                st.exception(e)

    # フッター
    st.markdown("---")
    st.caption("林業財務分析システム v1.2.0 - AIチャット機能 | Powered by Gemini API")


if __name__ == "__main__":
    main()
