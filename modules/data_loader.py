"""
データ読み込みモジュール

月次損益計算書データの読み込みと前処理を担当します。
"""

import os
from pathlib import Path
from typing import List
import pandas as pd
import streamlit as st


def sort_years(years: List[str]) -> List[str]:
    """
    年度を正しい順序でソート（平成→令和）

    Args:
        years: 年度のリスト（例: ['R6', 'H27', 'R5']）

    Returns:
        list: ソートされた年度リスト（例: ['H27', 'R5', 'R6']）

    Examples:
        >>> sort_years(['R6', 'H27', 'H28', 'R5'])
        ['H27', 'H28', 'R5', 'R6']
    """
    heisei = sorted([y for y in years if y.startswith('H')],
                    key=lambda x: int(x[1:]))
    reiwa = sorted([y for y in years if y.startswith('R')],
                   key=lambda x: int(x[1:]))
    return heisei + reiwa


def get_available_years(data_dir: str = "data/monthly_pl") -> List[str]:
    """
    利用可能な年度のリストを返す

    Args:
        data_dir: 月次データディレクトリのパス

    Returns:
        list: 利用可能な年度のリスト（例: ['H27', 'H28', ..., 'R6']）

    Raises:
        FileNotFoundError: data_dirが存在しない場合
    """
    data_path = Path(data_dir)

    if not data_path.exists():
        raise FileNotFoundError(f"データディレクトリが見つかりません: {data_dir}")

    # {年度}_monthly.csv 形式のファイルを検索
    csv_files = list(data_path.glob("*_monthly.csv"))

    if not csv_files:
        return []

    # ファイル名から年度を抽出
    years = []
    for file_path in csv_files:
        # 例: "R6_monthly.csv" -> "R6"
        filename = file_path.stem  # 拡張子を除く
        year = filename.replace("_monthly", "")
        years.append(year)

    # ソートして返す
    return sort_years(years)


def load_account_master(config_dir: str = "config") -> pd.DataFrame:
    """
    科目マスタを読み込む

    Args:
        config_dir: 設定ファイルディレクトリのパス

    Returns:
        pd.DataFrame: 科目情報（コード、名称、分類等）
        列: ['科目コード', '科目名', '大分類', '中分類', '固定費区分', '表示順']

    Raises:
        FileNotFoundError: account_master.csvが存在しない場合
    """
    master_path = Path(config_dir) / "account_master.csv"

    if not master_path.exists():
        raise FileNotFoundError(f"科目マスタが見つかりません: {master_path}")

    try:
        # UTF-8で読み込み（マスタはUTF-8で作成することを推奨）
        df = pd.read_csv(master_path, encoding='utf-8')
    except UnicodeDecodeError:
        # Shift-JISでも試す
        df = pd.read_csv(master_path, encoding='shift-jis')

    # 表示順でソート
    if '表示順' in df.columns:
        df = df.sort_values('表示順').reset_index(drop=True)

    return df


def load_monthly_data(data_dir: str = "data/monthly_pl") -> pd.DataFrame:
    """
    全年度の月次データを読み込み、統合したDataFrameを返す

    Args:
        data_dir: 月次データディレクトリのパス

    Returns:
        pd.DataFrame: 統合された月次データ
        列: ['年度', '科目コード', '科目名称', '4月', '5月', ..., '3月', '年間合計']

    Raises:
        FileNotFoundError: data_dirが存在しない場合
        ValueError: CSVファイルの形式が不正な場合

    Examples:
        >>> df = load_monthly_data()
        >>> df.columns
        Index(['年度', '科目コード', '科目名称', '4月', '5月', ..., '3月', '年間合計'], dtype='object')
    """
    data_path = Path(data_dir)

    if not data_path.exists():
        raise FileNotFoundError(f"データディレクトリが見つかりません: {data_dir}")

    # 利用可能な年度を取得
    available_years = get_available_years(data_dir)

    if not available_years:
        raise ValueError(f"データファイルが見つかりません: {data_dir}")

    all_data = []

    for year in available_years:
        csv_path = data_path / f"{year}_monthly.csv"

        try:
            # Shift-JISで読み込み（仕様通り）
            df = pd.read_csv(csv_path, encoding='shift-jis')

            # 必要な列を抽出
            # 列: タイトル,科目コード,科目名称,当月迄累計金額,当月迄累計構成比,4月,5月,...,3月
            required_columns = ['科目コード', '科目名称', '4月', '5月', '6月', '7月',
                              '8月', '9月', '10月', '11月', '12月', '1月', '2月', '3月']

            # 列の存在チェック
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                st.warning(f"{year}: 列が不足しています: {missing_cols}")
                continue

            # 必要な列のみ抽出
            df_selected = df[required_columns].copy()

            # 年度列を追加
            df_selected.insert(0, '年度', year)

            # 月次データを数値型に変換（欠損値は0）
            month_columns = ['4月', '5月', '6月', '7月', '8月', '9月',
                           '10月', '11月', '12月', '1月', '2月', '3月']
            for col in month_columns:
                df_selected[col] = pd.to_numeric(df_selected[col], errors='coerce').fillna(0)

            # 年間合計を計算
            df_selected['年間合計'] = df_selected[month_columns].sum(axis=1)

            # 科目コードを整数型に変換
            df_selected['科目コード'] = pd.to_numeric(df_selected['科目コード'], errors='coerce')

            # 欠損値を除外
            df_selected = df_selected.dropna(subset=['科目コード'])
            df_selected['科目コード'] = df_selected['科目コード'].astype(int)

            all_data.append(df_selected)

        except Exception as e:
            st.error(f"{year}のデータ読み込みエラー: {e}")
            continue

    if not all_data:
        raise ValueError("読み込めるデータファイルがありません")

    # 全データを結合
    result = pd.concat(all_data, ignore_index=True)

    # 年度順にソート
    year_order = {year: i for i, year in enumerate(sort_years(result['年度'].unique()))}
    result['_year_order'] = result['年度'].map(year_order)
    result = result.sort_values(['_year_order', '科目コード']).drop('_year_order', axis=1)
    result = result.reset_index(drop=True)

    return result


@st.cache_data(ttl=None)  # アプリ起動中ずっと保持
def load_all_data(data_dir: str = "data/monthly_pl") -> pd.DataFrame:
    """
    全データを読み込む（キャッシュ付き）

    Streamlitアプリケーション内での使用を想定。
    データの再読み込みを最小限にするため、アプリ起動中ずっとキャッシュします。

    Args:
        data_dir: 月次データディレクトリのパス

    Returns:
        pd.DataFrame: 統合された月次データ
    """
    return load_monthly_data(data_dir)


@st.cache_data
def load_master_cached(config_dir: str = "config") -> pd.DataFrame:
    """
    科目マスタを読み込む（キャッシュ付き）

    Streamlitアプリケーション内での使用を想定。

    Args:
        config_dir: 設定ファイルディレクトリのパス

    Returns:
        pd.DataFrame: 科目情報
    """
    return load_account_master(config_dir)


# ===== BS（貸借対照表）用関数 =====

def get_available_bs_years(data_dir: str = "data/monthly_bs") -> List[str]:
    """
    利用可能なBS年度のリストを返す

    Args:
        data_dir: BS月次データディレクトリのパス

    Returns:
        list: 利用可能な年度のリスト（例: ['H27', 'H28', ..., 'R6']）

    Raises:
        FileNotFoundError: data_dirが存在しない場合
    """
    data_path = Path(data_dir)

    if not data_path.exists():
        raise FileNotFoundError(f"データディレクトリが見つかりません: {data_dir}")

    # {年度}_monthly_bs.csv 形式のファイルを検索
    csv_files = list(data_path.glob("*_monthly_bs.csv"))

    if not csv_files:
        return []

    # ファイル名から年度を抽出
    years = []
    for file_path in csv_files:
        # 例: "R6_monthly_bs.csv" -> "R6"
        filename = file_path.stem  # 拡張子を除く
        year = filename.replace("_monthly_bs", "")
        years.append(year)

    # ソートして返す
    return sort_years(years)


def load_bs_account_master(config_dir: str = "config") -> pd.DataFrame:
    """
    BS科目マスタを読み込む

    Args:
        config_dir: 設定ファイルディレクトリのパス

    Returns:
        pd.DataFrame: BS科目情報（コード、名称、分類等）
        列: ['科目コード', '科目名', '大分類', '中分類', '表示順']

    Raises:
        FileNotFoundError: bs_account_master.csvが存在しない場合
    """
    master_path = Path(config_dir) / "bs_account_master.csv"

    if not master_path.exists():
        raise FileNotFoundError(f"BS科目マスタが見つかりません: {master_path}")

    try:
        # UTF-8で読み込み（マスタはUTF-8で作成することを推奨）
        df = pd.read_csv(master_path, encoding='utf-8')
    except UnicodeDecodeError:
        # Shift-JISでも試す
        df = pd.read_csv(master_path, encoding='shift-jis')

    # 表示順でソート
    if '表示順' in df.columns:
        df = df.sort_values('表示順').reset_index(drop=True)

    return df


def load_bs_monthly_data(data_dir: str = "data/monthly_bs") -> pd.DataFrame:
    """
    全年度のBS月次データを読み込み、統合したDataFrameを返す

    Args:
        data_dir: BS月次データディレクトリのパス

    Returns:
        pd.DataFrame: 統合されたBS月次データ
        列: ['年度', '科目コード', '科目名称', '4月', '5月', ..., '3月', '年間合計']

    Raises:
        FileNotFoundError: data_dirが存在しない場合
        ValueError: CSVファイルの形式が不正な場合

    Notes:
        - BSデータは「当月残高」列を使用（PLの「当月迄累計金額」とは異なる）
        - 列名: 「4月（当月残高）」→「4月」に変換
    """
    data_path = Path(data_dir)

    if not data_path.exists():
        raise FileNotFoundError(f"データディレクトリが見つかりません: {data_dir}")

    # 利用可能な年度を取得
    available_years = get_available_bs_years(data_dir)

    if not available_years:
        raise ValueError(f"データファイルが見つかりません: {data_dir}")

    all_data = []

    for year in available_years:
        csv_path = data_path / f"{year}_monthly_bs.csv"

        try:
            # Shift-JISで読み込み（仕様通り）
            df = pd.read_csv(csv_path, encoding='shift-jis')

            # 「当月残高」を含む列を抽出（4月〜3月）
            balance_columns = {}
            month_names = ['4月', '5月', '6月', '7月', '8月', '9月',
                          '10月', '11月', '12月', '1月', '2月', '3月']

            for month in month_names:
                # 列名例: "4月(当月残高)", "4月（当月残高）"など
                candidates = [col for col in df.columns if month in col and '当月残高' in col]
                if candidates:
                    balance_columns[month] = candidates[0]

            # 必要な列の存在チェック
            # 注: BSファイルは「コード」列を使用（「科目コード」ではない）
            required_base_columns = ['コード', '科目名称']
            missing_cols = [col for col in required_base_columns if col not in df.columns]

            if missing_cols:
                st.warning(f"{year}: 列が不足しています: {missing_cols}")
                continue

            if len(balance_columns) != 12:
                st.warning(f"{year}: 月次残高列が不足しています（{len(balance_columns)}/12列）")
                continue

            # データフレームを作成
            df_selected = pd.DataFrame()
            df_selected['科目コード'] = df['コード']  # BSファイルは「コード」列を使用
            df_selected['科目名称'] = df['科目名称']

            # 月次残高データを追加（列名を統一）
            for month in month_names:
                original_col = balance_columns[month]
                df_selected[month] = pd.to_numeric(df[original_col], errors='coerce').fillna(0)

            # 年度列を追加
            df_selected.insert(0, '年度', year)

            # 年間合計を計算（参考値: 各月残高の合計）
            df_selected['年間合計'] = df_selected[month_names].sum(axis=1)

            # 科目コードを整数型に変換
            df_selected['科目コード'] = pd.to_numeric(df_selected['科目コード'], errors='coerce')

            # 欠損値を除外
            df_selected = df_selected.dropna(subset=['科目コード'])
            df_selected['科目コード'] = df_selected['科目コード'].astype(int)

            # BS科目のみ抽出（コード111-399, 920）
            # コード400-899は損益科目、9500番台以降は合計行のため除外
            df_selected = df_selected[
                ((df_selected['科目コード'] >= 111) & (df_selected['科目コード'] <= 399)) |
                (df_selected['科目コード'] == 920)
            ]

            all_data.append(df_selected)

        except Exception as e:
            st.error(f"{year}のBSデータ読み込みエラー: {e}")
            continue

    if not all_data:
        raise ValueError("読み込めるBSデータファイルがありません")

    # 全データを結合
    result = pd.concat(all_data, ignore_index=True)

    # 年度順にソート
    year_order = {year: i for i, year in enumerate(sort_years(result['年度'].unique()))}
    result['_year_order'] = result['年度'].map(year_order)
    result = result.sort_values(['_year_order', '科目コード']).drop('_year_order', axis=1)
    result = result.reset_index(drop=True)

    return result


@st.cache_data(ttl=None)  # アプリ起動中ずっと保持
def load_all_bs_data(data_dir: str = "data/monthly_bs") -> pd.DataFrame:
    """
    全BSデータを読み込む（キャッシュ付き）

    Streamlitアプリケーション内での使用を想定。
    データの再読み込みを最小限にするため、アプリ起動中ずっとキャッシュします。

    Args:
        data_dir: BS月次データディレクトリのパス

    Returns:
        pd.DataFrame: 統合されたBS月次データ
    """
    return load_bs_monthly_data(data_dir)


@st.cache_data
def load_bs_master_cached(config_dir: str = "config") -> pd.DataFrame:
    """
    BS科目マスタを読み込む（キャッシュ付き）

    Streamlitアプリケーション内での使用を想定。

    Args:
        config_dir: 設定ファイルディレクトリのパス

    Returns:
        pd.DataFrame: BS科目情報
    """
    return load_bs_account_master(config_dir)
