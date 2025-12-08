"""
グラフ描画モジュール

Plotlyを使用した月次推移グラフの作成を担当します。
"""

from typing import List, Optional
import pandas as pd
import plotly.graph_objects as go


# 年度ごとの色設定
YEAR_COLORS = {
    'H27': '#8c564b',
    'H28': '#e377c2',
    'H29': '#7f7f7f',
    'H30': '#bcbd22',
    'R1': '#17becf',
    'R2': '#9467bd',
    'R3': '#d62728',
    'R4': '#1f77b4',
    'R5': '#2ca02c',
    'R6': '#ff7f0e',
}


def create_monthly_trend_chart(
    df: pd.DataFrame,
    account_code: int,
    years: List[str],
    account_name: Optional[str] = None,
    df_master: Optional[pd.DataFrame] = None,
    category_filter: Optional[str] = None
) -> go.Figure:
    """
    月次推移の折れ線グラフを作成

    Args:
        df: 月次データ（data_loaderの出力）
        account_code: 科目コード（合算時は0）
        years: 表示する年度のリスト
        account_name: 科目名（グラフタイトル用、Noneの場合はdfから取得）
        df_master: 科目マスタ（合算時に使用）
        category_filter: 大分類フィルタ（'収益'または'費用'）

    Returns:
        plotly.graph_objects.Figure: 月次推移グラフ

    Examples:
        >>> fig = create_monthly_trend_chart(df, 410, ['R5', 'R6'], '売上高')
        >>> fig.show()
    """
    # 月のリスト
    months = ['4月', '5月', '6月', '7月', '8月', '9月',
              '10月', '11月', '12月', '1月', '2月', '3月']

    # グラフオブジェクト作成
    fig = go.Figure()

    # 科目名を取得（未指定の場合）
    if account_name is None:
        if category_filter:
            account_name = f"大分類：{category_filter}（合算）"
        else:
            account_data = df[df['科目コード'] == account_code]
            if not account_data.empty:
                account_name = account_data.iloc[0]['科目名称']
            else:
                account_name = f"科目コード {account_code}"

    # 年度ごとにデータを追加
    for year in years:
        # 合算の場合
        if category_filter and df_master is not None:
            # マスタから該当大分類の科目コードを取得
            category_codes = df_master[df_master['大分類'] == category_filter]['科目コード'].tolist()

            # 該当年度・該当科目のデータを抽出して合算
            year_data = df[(df['年度'] == year) & (df['科目コード'].isin(category_codes))]

            if year_data.empty:
                continue

            # 月次データを合算
            monthly_values = []
            for month in months:
                total = year_data[month].sum() if month in year_data.columns else 0
                monthly_values.append(total)
        else:
            # 通常の単一科目の場合
            year_data = df[(df['年度'] == year) & (df['科目コード'] == account_code)]

            if year_data.empty:
                continue

            # 月次データを取得
            monthly_values = []
            for month in months:
                value = year_data[month].values[0] if month in year_data.columns else 0
                monthly_values.append(value)

        # 線の色を取得（未定義の年度はデフォルト色）
        color = YEAR_COLORS.get(year, '#333333')

        # トレースを追加
        fig.add_trace(go.Scatter(
            x=months,
            y=monthly_values,
            mode='lines+markers',
            name=year,
            line=dict(color=color, width=2),
            marker=dict(size=6),
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         '%{x}: %{y:,.0f}円<br>' +
                         '<extra></extra>'
        ))

    # レイアウト設定
    fig.update_layout(
        title={
            'text': f"{account_name} - 月次推移",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'family': 'Arial, sans-serif'}
        },
        xaxis=dict(
            title='月',
            tickangle=0,
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title='金額（円）',
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            tickformat=',.0f'
        ),
        hovermode='x unified',
        legend=dict(
            orientation='v',
            yanchor='top',
            y=1,
            xanchor='left',
            x=1.02,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='gray',
            borderwidth=1
        ),
        plot_bgcolor='white',
        height=500,
        margin=dict(l=80, r=150, t=80, b=60)
    )

    # グリッド線の設定
    fig.update_xaxes(showline=True, linewidth=1, linecolor='gray', mirror=True)
    fig.update_yaxes(showline=True, linewidth=1, linecolor='gray', mirror=True)

    return fig


def create_comparison_table(
    df: pd.DataFrame,
    account_code: int,
    years: List[str],
    df_master: Optional[pd.DataFrame] = None,
    category_filter: Optional[str] = None
) -> pd.DataFrame:
    """
    年度比較テーブルを作成

    Args:
        df: 月次データ
        account_code: 科目コード（合算時は0）
        years: 表示する年度のリスト
        df_master: 科目マスタ（合算時に使用）
        category_filter: 大分類フィルタ（'収益'または'費用'）

    Returns:
        pd.DataFrame: 比較テーブル（列: 年度, 4月, ..., 3月, 年間合計, 前年比）
    """
    months = ['4月', '5月', '6月', '7月', '8月', '9月',
              '10月', '11月', '12月', '1月', '2月', '3月']

    result_data = []

    for i, year in enumerate(years):
        # 合算の場合
        if category_filter and df_master is not None:
            # マスタから該当大分類の科目コードを取得
            category_codes = df_master[df_master['大分類'] == category_filter]['科目コード'].tolist()

            # 該当年度・該当科目のデータを抽出
            year_data = df[(df['年度'] == year) & (df['科目コード'].isin(category_codes))]

            if year_data.empty:
                continue

            row = {'年度': year}

            # 月次データを合算
            for month in months:
                total = year_data[month].sum() if month in year_data.columns else 0
                row[month] = total

            # 年間合計を合算
            row['年間合計'] = year_data['年間合計'].sum()
        else:
            # 通常の単一科目の場合
            year_data = df[(df['年度'] == year) & (df['科目コード'] == account_code)]

            if year_data.empty:
                continue

            row = {'年度': year}

            # 月次データを追加
            for month in months:
                value = year_data[month].values[0] if month in year_data.columns else 0
                row[month] = value

            # 年間合計
            row['年間合計'] = year_data['年間合計'].values[0]

        # 前年比を計算（前年度がある場合）
        if len(result_data) > 0:
            prev_year_row = result_data[-1]
            prev_total = prev_year_row['年間合計']
            current_total = row['年間合計']
            if prev_total != 0:
                row['前年比'] = ((current_total - prev_total) / prev_total) * 100
            else:
                row['前年比'] = None
        else:
            row['前年比'] = None

        result_data.append(row)

    # DataFrameに変換
    result_df = pd.DataFrame(result_data)

    return result_df


def format_currency(value: float) -> str:
    """
    金額を3桁カンマ区切りでフォーマット

    Args:
        value: 金額

    Returns:
        str: フォーマットされた金額文字列

    Examples:
        >>> format_currency(1234567)
        '1,234,567'
    """
    return f"{int(value):,}"


def format_percentage(value: Optional[float]) -> str:
    """
    パーセンテージをフォーマット

    Args:
        value: パーセンテージ値

    Returns:
        str: フォーマットされたパーセンテージ文字列

    Examples:
        >>> format_percentage(15.5)
        '+15.5%'
        >>> format_percentage(-5.2)
        '-5.2%'
    """
    if value is None or pd.isna(value):
        return '-'

    sign = '+' if value > 0 else ''
    return f"{sign}{value:.1f}%"
