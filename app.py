"""
林業財務分析アプリケーション - トップページ

月次損益計算書（PL）・貸借対照表（BS）の可視化・分析、
AIチャット機能による財務データ分析を提供します。
"""

import streamlit as st
from pathlib import Path


# ページ設定
st.set_page_config(
    page_title="林業財務分析システム",
    page_icon="🌲",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    """トップページのメイン処理"""

    # タイトル
    st.title("🌲 林業財務分析システム")
    st.markdown("月次財務データの可視化・分析、AIチャット機能")
    st.markdown("---")

    # 概要
    st.header("📊 システム概要")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📈 PL分析")
        st.markdown("""
        **損益計算書（PL）の可視化**
        - 月次推移グラフ
        - 複数年度比較（最大5年度）
        - 3階層集計（個別科目、中分類、大分類）
        - CSV/Excelエクスポート
        """)

        if st.button("PL分析を開く", use_container_width=True, type="primary"):
            st.switch_page("pages/1_📊_PL分析.py")

    with col2:
        st.subheader("💰 BS分析")
        st.markdown("""
        **貸借対照表（BS）の可視化**
        - 月次残高推移グラフ
        - 複数年度比較（最大5年度）
        - 3階層集計（個別科目、中分類、大分類）
        - CSV/Excelエクスポート
        """)

        if st.button("BS分析を開く", use_container_width=True, type="primary"):
            st.switch_page("pages/2_💰_BS分析.py")

    with col3:
        st.subheader("💬 AIチャット")
        st.markdown("""
        **自然言語での財務分析**
        - Gemini APIによるコード生成
        - 動的データ参照（PL/BS 10年分）
        - グラフ・データ自動生成
        - 会話ログ保存（Markdown形式）
        """)

        if st.button("AIチャットを開く", use_container_width=True, type="primary"):
            st.switch_page("pages/3_💬_AIチャット.py")

    st.markdown("---")

    # データ状態の確認
    st.header("📁 データ状態")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("PL（損益計算書）")
        pl_dir = Path("data/monthly_pl")
        if pl_dir.exists():
            pl_files = list(pl_dir.glob("*_monthly.csv"))
            st.success(f"✅ {len(pl_files)} 年度分のデータが利用可能")

            with st.expander("📋 利用可能な年度", expanded=False):
                for file in sorted(pl_files):
                    year = file.stem.replace("_monthly", "")
                    st.text(f"- {year}")
        else:
            st.warning("⚠️ PLデータディレクトリが見つかりません")
            st.info("data/monthly_pl/ を作成し、月次データを配置してください")

    with col2:
        st.subheader("BS（貸借対照表）")
        bs_dir = Path("data/monthly_bs")
        if bs_dir.exists():
            bs_files = list(bs_dir.glob("*_monthly_bs.csv"))
            st.success(f"✅ {len(bs_files)} 年度分のデータが利用可能")

            with st.expander("📋 利用可能な年度", expanded=False):
                for file in sorted(bs_files):
                    year = file.stem.replace("_monthly_bs", "")
                    st.text(f"- {year}")
        else:
            st.warning("⚠️ BSデータディレクトリが見つかりません")
            st.info("data/monthly_bs/ を作成し、月次データを配置してください")

    st.markdown("---")

    # 使い方
    st.header("📖 使い方")

    with st.expander("1️⃣ PL/BS分析の使い方", expanded=False):
        st.markdown("""
        ### PL/BS分析ページの使い方

        1. **科目選択**: サイドバーから分析する科目を選択
           - 個別科目: 特定の科目（例: 売上高、役員報酬）
           - 中分類合算: 複数科目の合計（例: 製造原価、販管費）
           - 大分類合算: さらに大きな分類（例: 収益、費用）

        2. **年度選択**: 比較する年度を選択（最大5年度）

        3. **グラフ確認**: 月次推移グラフで傾向を把握

        4. **データテーブル**: 詳細な数値を確認

        5. **エクスポート**: CSV/Excel形式でダウンロード
        """)

    with st.expander("2️⃣ AIチャットの使い方", expanded=False):
        st.markdown("""
        ### AIチャット機能の使い方

        1. **セッション開始**: サイドバーから「🆕 新規セッション開始」をクリック

        2. **モデル選択**:
           - Gemini 2.5 Flash（バランス・推奨）: 一般的な分析
           - Gemini 2.5 Pro（高度な分析）: 複雑な予測・推論

        3. **質問入力**: 自然言語で財務データについて質問
           - 例: 「R6の売上高を教えて」
           - 例: 「R6とR5の借入返済額を比較して」
           - 例: 「過去5年間の役員報酬推移をグラフ化して」

        4. **コード確認**: 生成されたPythonコードを確認

        5. **実行**: 「▶️ 実行」ボタンで結果を表示

        6. **保存**: 「💾 会話を保存」で会話履歴をMarkdown形式で保存
        """)

    with st.expander("3️⃣ 参考資料のアップロード", expanded=False):
        st.markdown("""
        ### 参考資料アップロード機能

        AIチャットでは、追加の財務資料をアップロードして分析に活用できます。

        **対応形式**: CSV, Excel (.xlsx)

        **アップロード手順**:
        1. AIチャットページを開く
        2. サイドバーの「2. 参考資料アップロード」からファイルを選択
        3. アップロードされたファイルはAIが自動で認識し、分析に使用

        **例**:
        - 資金繰表.xlsx
        - 経営計画.csv
        - 補助金申請資料.xlsx
        """)

    st.markdown("---")

    # システム情報
    st.header("ℹ️ システム情報")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **バージョン**: 1.2.0
        **実装機能**:
        - PL分析（Phase 1）
        - BS分析（Phase 1.5）
        - AIチャット（Phase 2）
        """)

    with col2:
        st.markdown("""
        **技術スタック**:
        - Frontend: Streamlit
        - Visualization: Plotly
        - AI: Gemini API (Google)
        - Data: pandas, numpy
        """)

    st.markdown("---")

    # フッター
    st.caption("🌲 林業財務分析システム v1.2.0 | Powered by Streamlit & Gemini API")


if __name__ == "__main__":
    main()
