"""
林業財務分析アプリケーション

月次損益計算書データの可視化と分析を行うStreamlitアプリケーション
"""

import streamlit as st
import pandas as pd
from pathlib import Path

from modules import (
    load_all_data,
    load_master_cached,
    get_available_years,
    sort_years,
    create_monthly_trend_chart,
    export_to_csv,
    export_to_excel,
)
from modules.visualizer import create_comparison_table, format_currency, format_percentage
from modules.exporter import create_download_filename

# BS用のインポート
from modules.data_loader import (
    load_all_bs_data,
    load_bs_master_cached,
    get_available_bs_years,
)
from modules.visualizer import (
    create_bs_monthly_trend_chart,
    create_bs_comparison_table,
)


# ページ設定
st.set_page_config(
    page_title="林業財務分析",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


def render_pl_tab():
    """PL（損益計算書）タブのレンダリング"""

    # データディレクトリの確認
    data_dir = "data/monthly_pl"
    config_dir = "config"

    if not Path(data_dir).exists():
        st.error(f"データディレクトリが見つかりません: {data_dir}")
        st.info("data/monthly_pl ディレクトリに月次データ（{年度}_monthly.csv）を配置してください。")
        st.stop()

    # データ読み込み
    try:
        with st.spinner("データを読み込んでいます..."):
            # 月次データ読み込み
            df_monthly = load_all_data(data_dir)

            # 科目マスタ読み込み
            try:
                df_master = load_master_cached(config_dir)
            except FileNotFoundError:
                st.warning("科目マスタが見つかりません。データのみで表示します。")
                df_master = None

            # 利用可能な年度を取得
            available_years = get_available_years(data_dir)

    except FileNotFoundError as e:
        st.error(f"エラー: {e}")
        st.stop()
    except ValueError as e:
        st.error(f"データ読み込みエラー: {e}")
        st.stop()
    except Exception as e:
        st.error(f"予期しないエラー: {e}")
        st.exception(e)
        st.stop()

    # サイドバー
    with st.sidebar:
        st.header("⚙️ 設定")

        # 科目選択
        st.subheader("1. 科目選択")

        # 科目リストの作成
        if df_master is not None:
            # 大分類の合算オプションを追加
            account_options = [
                {
                    'code': 0,
                    'name': '大分類：収益（合算）',
                    'category': '収益',
                    'subcategory': None,
                    'display': '📊 大分類：収益（合算）',
                    'is_summary': True,
                    'summary_type': 'category',
                    'category_filter': '収益',
                    'subcategory_filter': None
                },
                {
                    'code': 0,
                    'name': '大分類：費用（合算）',
                    'category': '費用',
                    'subcategory': None,
                    'display': '📊 大分類：費用（合算）',
                    'is_summary': True,
                    'summary_type': 'category',
                    'category_filter': '費用',
                    'subcategory_filter': None
                }
            ]

            # 中分類の合算オプションを追加
            subcategory_list = [
                ('製造原価', '費用'),
                ('販管費', '費用'),
                ('営業外収益', '収益'),
                ('営業外費用', '費用'),
                ('特別損失', '費用')
            ]

            for subcat, cat in subcategory_list:
                account_options.append({
                    'code': 0,
                    'name': f'中分類：{subcat}（合算）',
                    'category': cat,
                    'subcategory': subcat,
                    'display': f'📈 中分類：{subcat}（合算）',
                    'is_summary': True,
                    'summary_type': 'subcategory',
                    'category_filter': None,
                    'subcategory_filter': subcat
                })

            # マスタから科目リストを作成
            for _, row in df_master.iterrows():
                code = int(row['科目コード'])
                name = row['科目名']
                category = row.get('大分類', '')
                subcategory = row.get('中分類', '')
                account_options.append({
                    'code': code,
                    'name': name,
                    'category': category,
                    'subcategory': subcategory,
                    'display': f"{name} ({code}) - {category}",
                    'is_summary': False,
                    'summary_type': None,
                    'category_filter': None,
                    'subcategory_filter': None
                })
        else:
            # データから科目リストを作成
            unique_accounts = df_monthly[['科目コード', '科目名称']].drop_duplicates()
            account_options = []
            for _, row in unique_accounts.iterrows():
                code = int(row['科目コード'])
                name = row['科目名称']
                account_options.append({
                    'code': code,
                    'name': name,
                    'category': '',
                    'display': f"{name} ({code})",
                    'is_summary': False,
                    'category_filter': None
                })

        # 科目選択ドロップダウン
        selected_account_display = st.selectbox(
            "分析する科目を選択",
            options=[opt['display'] for opt in account_options],
            index=0,
            key="pl_account_select"
        )

        # 選択された科目の情報を取得
        selected_account = next(
            opt for opt in account_options
            if opt['display'] == selected_account_display
        )
        account_code = selected_account['code']
        account_name = selected_account['name']
        is_summary = selected_account.get('is_summary', False)
        summary_type = selected_account.get('summary_type', None)
        category_filter = selected_account.get('category_filter', None)
        subcategory_filter = selected_account.get('subcategory_filter', None)

        st.markdown("---")

        # 年度選択
        st.subheader("2. 年度選択")
        st.caption("最大5年度まで選択可能")

        selected_years = st.multiselect(
            "比較する年度を選択",
            options=available_years,
            default=available_years[-2:] if len(available_years) >= 2 else available_years,
            max_selections=5,
            key="pl_year_select"
        )

        if not selected_years:
            st.warning("年度を選択してください")

        st.markdown("---")

        # エクスポート
        st.subheader("3. データエクスポート")

        if selected_years:
            # 比較テーブルを作成
            comparison_df = create_comparison_table(
                df_monthly,
                account_code,
                selected_years,
                df_master=df_master,
                category_filter=category_filter,
                subcategory_filter=subcategory_filter
            )

            # CSV出力
            csv_data = export_to_csv(comparison_df)
            csv_filename = create_download_filename(account_name, 'csv')

            st.download_button(
                label="📥 CSV ダウンロード",
                data=csv_data,
                file_name=csv_filename,
                mime="text/csv",
                use_container_width=True,
                key="pl_csv_download"
            )

            # Excel出力
            excel_data = export_to_excel(comparison_df, sheet_name=account_name)
            excel_filename = create_download_filename(account_name, 'excel')

            st.download_button(
                label="📥 Excel ダウンロード",
                data=excel_data,
                file_name=excel_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="pl_excel_download"
            )

        st.markdown("---")

        # 情報表示
        st.caption(f"📁 利用可能年度: {len(available_years)}年度")
        st.caption(f"📊 科目数: {len(account_options)}科目")

    # メインエリア
    if not selected_years:
        st.info("👈 サイドバーから年度を選択してください")
        st.stop()

    # 科目情報表示
    if is_summary:
        st.subheader(f"📈 {account_name}")

        # 中分類での合算の場合
        if df_master is not None and subcategory_filter:
            category_accounts = df_master[df_master['中分類'] == subcategory_filter][
                ['科目コード', '科目名', '大分類']
            ].sort_values('科目コード')

            st.info(f"該当科目数: {len(category_accounts)}科目")

            # 科目リストを展開可能な形式で表示
            with st.expander("📋 含まれる科目の一覧", expanded=False):
                # 科目リストをテーブル形式で表示
                display_accounts = category_accounts.copy()
                display_accounts.columns = ['科目コード', '科目名称', '大分類']

                st.dataframe(
                    display_accounts,
                    use_container_width=True,
                    hide_index=True
                )
        # 大分類での合算の場合
        elif df_master is not None and category_filter:
            category_accounts = df_master[df_master['大分類'] == category_filter][
                ['科目コード', '科目名', '中分類']
            ].sort_values('科目コード')

            st.info(f"該当科目数: {len(category_accounts)}科目")

            # 科目リストを展開可能な形式で表示
            with st.expander("📋 含まれる科目の一覧", expanded=False):
                # 科目リストをテーブル形式で表示
                display_accounts = category_accounts.copy()
                display_accounts.columns = ['科目コード', '科目名称', '中分類']

                st.dataframe(
                    display_accounts,
                    use_container_width=True,
                    hide_index=True
                )
    else:
        st.subheader(f"📈 {account_name} ({account_code})")

        if df_master is not None:
            # マスタ情報があれば表示
            master_info = df_master[df_master['科目コード'] == account_code]
            if not master_info.empty:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("大分類", master_info.iloc[0].get('大分類', '-'))
                with col2:
                    st.metric("中分類", master_info.iloc[0].get('中分類', '-'))
                with col3:
                    st.metric("固定費区分", master_info.iloc[0].get('固定費区分', '-'))

    st.markdown("---")

    # グラフ表示
    st.subheader("📊 月次推移グラフ")

    try:
        fig = create_monthly_trend_chart(
            df_monthly,
            account_code,
            selected_years,
            account_name,
            df_master=df_master,
            category_filter=category_filter,
            subcategory_filter=subcategory_filter
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"グラフ作成エラー: {e}")
        st.exception(e)

    st.markdown("---")

    # データテーブル表示
    st.subheader("📋 データテーブル")

    try:
        comparison_df = create_comparison_table(
            df_monthly,
            account_code,
            selected_years,
            df_master=df_master,
            category_filter=category_filter,
            subcategory_filter=subcategory_filter
        )

        if comparison_df.empty:
            st.warning("表示するデータがありません")
        else:
            # データフレームを表示用に整形
            display_df = comparison_df.copy()

            # 月度ごとの平均値を計算（年度行のみ対象）
            months_only = ['4月', '5月', '6月', '7月', '8月', '9月',
                          '10月', '11月', '12月', '1月', '2月', '3月']

            # 年度行を抽出（年間合計がある行）
            if '年間合計' in display_df.columns:
                year_rows = display_df[display_df['年間合計'].notna()].copy()

                if not year_rows.empty:
                    # 平均値行を作成
                    avg_row = {'年度': '月度平均'}

                    for month in months_only:
                        if month in year_rows.columns:
                            # 数値データのみを抽出して平均を計算
                            numeric_values = pd.to_numeric(year_rows[month], errors='coerce')
                            avg_value = numeric_values.mean()
                            avg_row[month] = avg_value if pd.notna(avg_value) else 0

                    # 年間合計の平均
                    if '年間合計' in year_rows.columns:
                        numeric_total = pd.to_numeric(year_rows['年間合計'], errors='coerce')
                        avg_row['年間合計'] = numeric_total.mean()

                    # 前年比は空欄
                    if '前年比' in display_df.columns:
                        avg_row['前年比'] = None

                    # 平均行をDataFrameに追加
                    avg_df = pd.DataFrame([avg_row])
                    display_df = pd.concat([display_df, avg_df], ignore_index=True)

            # 月次データを3桁カンマ区切りでフォーマット
            months = ['4月', '5月', '6月', '7月', '8月', '9月',
                     '10月', '11月', '12月', '1月', '2月', '3月', '年間合計']

            for month in months:
                if month in display_df.columns:
                    display_df[month] = display_df[month].apply(
                        lambda x: format_currency(x) if pd.notna(x) else '-'
                    )

            # 前年比をフォーマット
            if '前年比' in display_df.columns:
                display_df['前年比'] = display_df['前年比'].apply(
                    lambda x: format_percentage(x) if pd.notna(x) else '-'
                )

            # スタイル付きで表示
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )

            # 統計情報
            st.markdown("#### 📊 統計情報")
            col1, col2, col3 = st.columns(3)

            with col1:
                latest_year = selected_years[-1]
                latest_data = comparison_df[comparison_df['年度'] == latest_year]
                if not latest_data.empty:
                    latest_total = latest_data['年間合計'].values[0]
                    st.metric("最新年度合計", format_currency(latest_total), delta=f"{latest_year}")

            with col2:
                if len(selected_years) >= 2:
                    prev_year = selected_years[-2]
                    prev_data = comparison_df[comparison_df['年度'] == prev_year]
                    if not prev_data.empty:
                        prev_total = prev_data['年間合計'].values[0]
                        st.metric("前年度合計", format_currency(prev_total), delta=f"{prev_year}")

            with col3:
                if len(selected_years) >= 2:
                    latest_data = comparison_df[comparison_df['年度'] == selected_years[-1]]
                    if not latest_data.empty and '前年比' in latest_data.columns:
                        yoy_change = latest_data['前年比'].values[0]
                        if pd.notna(yoy_change):
                            st.metric("前年比", format_percentage(yoy_change), delta=format_percentage(yoy_change))

    except Exception as e:
        st.error(f"テーブル作成エラー: {e}")
        st.exception(e)


def render_bs_tab():
    """BS（貸借対照表）タブのレンダリング"""

    # データディレクトリの確認
    data_dir = "data/monthly_bs"
    config_dir = "config"

    if not Path(data_dir).exists():
        st.error(f"データディレクトリが見つかりません: {data_dir}")
        st.info("data/monthly_bs ディレクトリに月次データ（{年度}_monthly_bs.csv）を配置してください。")
        st.stop()

    # データ読み込み
    try:
        with st.spinner("BSデータを読み込んでいます..."):
            # BS月次データ読み込み
            df_monthly = load_all_bs_data(data_dir)

            # BS科目マスタ読み込み
            try:
                df_master = load_bs_master_cached(config_dir)
            except FileNotFoundError:
                st.warning("BS科目マスタが見つかりません。データのみで表示します。")
                df_master = None

            # 利用可能な年度を取得
            available_years = get_available_bs_years(data_dir)

    except FileNotFoundError as e:
        st.error(f"エラー: {e}")
        st.stop()
    except ValueError as e:
        st.error(f"データ読み込みエラー: {e}")
        st.stop()
    except Exception as e:
        st.error(f"予期しないエラー: {e}")
        st.exception(e)
        st.stop()

    # サイドバー
    with st.sidebar:
        st.header("⚙️ BS設定")

        # 科目選択
        st.subheader("1. BS科目選択")

        # 科目リストの作成
        if df_master is not None:
            # 大分類の合算オプションを追加
            account_options = [
                {
                    'code': 0,
                    'name': '大分類：流動資産（合算）',
                    'category': '流動資産',
                    'subcategory': None,
                    'display': '📊 大分類：流動資産（合算）',
                    'is_summary': True,
                    'summary_type': 'category',
                    'category_filter': '流動資産',
                    'subcategory_filter': None
                },
                {
                    'code': 0,
                    'name': '大分類：固定資産（合算）',
                    'category': '固定資産',
                    'subcategory': None,
                    'display': '📊 大分類：固定資産（合算）',
                    'is_summary': True,
                    'summary_type': 'category',
                    'category_filter': '固定資産',
                    'subcategory_filter': None
                },
                {
                    'code': 0,
                    'name': '大分類：流動負債（合算）',
                    'category': '流動負債',
                    'subcategory': None,
                    'display': '📊 大分類：流動負債（合算）',
                    'is_summary': True,
                    'summary_type': 'category',
                    'category_filter': '流動負債',
                    'subcategory_filter': None
                },
                {
                    'code': 0,
                    'name': '大分類：固定負債（合算）',
                    'category': '固定負債',
                    'subcategory': None,
                    'display': '📊 大分類：固定負債（合算）',
                    'is_summary': True,
                    'summary_type': 'category',
                    'category_filter': '固定負債',
                    'subcategory_filter': None
                },
                {
                    'code': 0,
                    'name': '大分類：純資産（合算）',
                    'category': '純資産',
                    'subcategory': None,
                    'display': '📊 大分類：純資産（合算）',
                    'is_summary': True,
                    'summary_type': 'category',
                    'category_filter': '純資産',
                    'subcategory_filter': None
                }
            ]

            # 中分類の合算オプションを追加
            subcategory_list = [
                ('現金及び預金', '流動資産'),
                ('その他流動資産', '流動資産'),
                ('有形固定資産', '固定資産'),
                ('無形固定資産', '固定資産'),
                ('投資その他の資産', '固定資産'),
                ('短期借入金', '流動負債'),
                ('その他流動負債', '流動負債'),
                ('長期借入金', '固定負債'),
                ('資本金', '純資産'),
                ('利益剰余金', '純資産')
            ]

            for subcat, cat in subcategory_list:
                account_options.append({
                    'code': 0,
                    'name': f'中分類：{subcat}（合算）',
                    'category': cat,
                    'subcategory': subcat,
                    'display': f'📈 中分類：{subcat}（合算）',
                    'is_summary': True,
                    'summary_type': 'subcategory',
                    'category_filter': None,
                    'subcategory_filter': subcat
                })

            # マスタから科目リストを作成
            for _, row in df_master.iterrows():
                code = int(row['科目コード'])
                name = row['科目名']
                category = row.get('大分類', '')
                subcategory = row.get('中分類', '')
                account_options.append({
                    'code': code,
                    'name': name,
                    'category': category,
                    'subcategory': subcategory,
                    'display': f"{name} ({code}) - {category}",
                    'is_summary': False,
                    'summary_type': None,
                    'category_filter': None,
                    'subcategory_filter': None
                })
        else:
            # データから科目リストを作成
            unique_accounts = df_monthly[['科目コード', '科目名称']].drop_duplicates()
            account_options = []
            for _, row in unique_accounts.iterrows():
                code = int(row['科目コード'])
                name = row['科目名称']
                account_options.append({
                    'code': code,
                    'name': name,
                    'category': '',
                    'display': f"{name} ({code})",
                    'is_summary': False,
                    'category_filter': None
                })

        # 科目選択ドロップダウン
        selected_account_display = st.selectbox(
            "分析するBS科目を選択",
            options=[opt['display'] for opt in account_options],
            index=0,
            key="bs_account_select"
        )

        # 選択された科目の情報を取得
        selected_account = next(
            opt for opt in account_options
            if opt['display'] == selected_account_display
        )
        account_code = selected_account['code']
        account_name = selected_account['name']
        is_summary = selected_account.get('is_summary', False)
        summary_type = selected_account.get('summary_type', None)
        category_filter = selected_account.get('category_filter', None)
        subcategory_filter = selected_account.get('subcategory_filter', None)

        st.markdown("---")

        # 年度選択
        st.subheader("2. 年度選択")
        st.caption("最大5年度まで選択可能")

        selected_years = st.multiselect(
            "比較する年度を選択",
            options=available_years,
            default=available_years[-2:] if len(available_years) >= 2 else available_years,
            max_selections=5,
            key="bs_year_select"
        )

        if not selected_years:
            st.warning("年度を選択してください")

        st.markdown("---")

        # エクスポート
        st.subheader("3. データエクスポート")

        if selected_years:
            # 比較テーブルを作成
            comparison_df = create_bs_comparison_table(
                df_monthly,
                account_code,
                selected_years,
                df_master=df_master,
                category_filter=category_filter,
                subcategory_filter=subcategory_filter
            )

            # CSV出力
            csv_data = export_to_csv(comparison_df)
            csv_filename = create_download_filename(f"BS_{account_name}", 'csv')

            st.download_button(
                label="📥 CSV ダウンロード",
                data=csv_data,
                file_name=csv_filename,
                mime="text/csv",
                use_container_width=True,
                key="bs_csv_download"
            )

            # Excel出力
            excel_data = export_to_excel(comparison_df, sheet_name=account_name[:31])
            excel_filename = create_download_filename(f"BS_{account_name}", 'excel')

            st.download_button(
                label="📥 Excel ダウンロード",
                data=excel_data,
                file_name=excel_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="bs_excel_download"
            )

        st.markdown("---")

        # 情報表示
        st.caption(f"📁 利用可能年度: {len(available_years)}年度")
        st.caption(f"📊 BS科目数: {len(account_options)}科目")

    # メインエリア
    if not selected_years:
        st.info("👈 サイドバーから年度を選択してください")
        st.stop()

    # 科目情報表示
    if is_summary:
        st.subheader(f"📈 {account_name}")

        # 中分類での合算の場合
        if df_master is not None and subcategory_filter:
            category_accounts = df_master[df_master['中分類'] == subcategory_filter][
                ['科目コード', '科目名', '大分類']
            ].sort_values('科目コード')

            st.info(f"該当科目数: {len(category_accounts)}科目")

            # 科目リストを展開可能な形式で表示
            with st.expander("📋 含まれる科目の一覧", expanded=False):
                # 科目リストをテーブル形式で表示
                display_accounts = category_accounts.copy()
                display_accounts.columns = ['科目コード', '科目名称', '大分類']

                st.dataframe(
                    display_accounts,
                    use_container_width=True,
                    hide_index=True
                )
        # 大分類での合算の場合
        elif df_master is not None and category_filter:
            category_accounts = df_master[df_master['大分類'] == category_filter][
                ['科目コード', '科目名', '中分類']
            ].sort_values('科目コード')

            st.info(f"該当科目数: {len(category_accounts)}科目")

            # 科目リストを展開可能な形式で表示
            with st.expander("📋 含まれる科目の一覧", expanded=False):
                # 科目リストをテーブル形式で表示
                display_accounts = category_accounts.copy()
                display_accounts.columns = ['科目コード', '科目名称', '中分類']

                st.dataframe(
                    display_accounts,
                    use_container_width=True,
                    hide_index=True
                )
    else:
        st.subheader(f"📈 {account_name} ({account_code})")

        if df_master is not None:
            # マスタ情報があれば表示
            master_info = df_master[df_master['科目コード'] == account_code]
            if not master_info.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("大分類", master_info.iloc[0].get('大分類', '-'))
                with col2:
                    st.metric("中分類", master_info.iloc[0].get('中分類', '-'))

    st.markdown("---")

    # グラフ表示
    st.subheader("📊 月次残高推移グラフ")

    try:
        fig = create_bs_monthly_trend_chart(
            df_monthly,
            account_code,
            selected_years,
            account_name,
            df_master=df_master,
            category_filter=category_filter,
            subcategory_filter=subcategory_filter
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"グラフ作成エラー: {e}")
        st.exception(e)

    st.markdown("---")

    # データテーブル表示
    st.subheader("📋 データテーブル")

    try:
        comparison_df = create_bs_comparison_table(
            df_monthly,
            account_code,
            selected_years,
            df_master=df_master,
            category_filter=category_filter,
            subcategory_filter=subcategory_filter
        )

        if comparison_df.empty:
            st.warning("表示するデータがありません")
        else:
            # データフレームを表示用に整形
            display_df = comparison_df.copy()

            # 月次データを3桁カンマ区切りでフォーマット
            months = ['4月', '5月', '6月', '7月', '8月', '9月',
                     '10月', '11月', '12月', '1月', '2月', '3月', '年間合計']

            for month in months:
                if month in display_df.columns:
                    display_df[month] = display_df[month].apply(
                        lambda x: format_currency(x) if pd.notna(x) else '-'
                    )

            # 前年比をフォーマット
            if '前年比' in display_df.columns:
                display_df['前年比'] = display_df['前年比'].apply(
                    lambda x: format_percentage(x) if pd.notna(x) else '-'
                )

            # スタイル付きで表示
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )

            # 統計情報
            st.markdown("#### 📊 統計情報")
            col1, col2, col3 = st.columns(3)

            with col1:
                latest_year = selected_years[-1]
                latest_data = comparison_df[comparison_df['年度'] == latest_year]
                if not latest_data.empty:
                    latest_total = latest_data['年間合計'].values[0]
                    st.metric("最新年度合計", format_currency(latest_total), delta=f"{latest_year}")

            with col2:
                if len(selected_years) >= 2:
                    prev_year = selected_years[-2]
                    prev_data = comparison_df[comparison_df['年度'] == prev_year]
                    if not prev_data.empty:
                        prev_total = prev_data['年間合計'].values[0]
                        st.metric("前年度合計", format_currency(prev_total), delta=f"{prev_year}")

            with col3:
                if len(selected_years) >= 2:
                    latest_data = comparison_df[comparison_df['年度'] == selected_years[-1]]
                    if not latest_data.empty and '前年比' in latest_data.columns:
                        yoy_change = latest_data['前年比'].values[0]
                        if pd.notna(yoy_change):
                            st.metric("前年比", format_percentage(yoy_change), delta=format_percentage(yoy_change))

    except Exception as e:
        st.error(f"テーブル作成エラー: {e}")
        st.exception(e)


def main():
    """メインアプリケーション"""

    # タイトル
    st.title("📊 林業財務分析システム")
    st.markdown("月次損益計算書（PL）・貸借対照表（BS）の可視化・分析")
    st.markdown("---")

    # タブUI
    tab1, tab2 = st.tabs(["📈 損益計算書 (PL)", "💰 貸借対照表 (BS)"])

    with tab1:
        render_pl_tab()

    with tab2:
        render_bs_tab()

    # フッター
    st.markdown("---")
    st.caption("林業財務分析システム v1.1.0 | Powered by Streamlit")


if __name__ == "__main__":
    main()
