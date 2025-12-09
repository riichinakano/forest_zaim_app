"""
BS機能の単体テストスクリプト

要件定義書の単体テストを実施:
- BSデータ読み込み
- BS科目マスタ読み込み
- 列名変換
- 年度ソート
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from modules.data_loader import (
    load_bs_monthly_data,
    load_bs_account_master,
    get_available_bs_years,
    sort_years
)


def test_bs_account_master():
    """BS科目マスタ読み込みテスト"""
    print("=" * 60)
    print("テスト1: BS科目マスタ読み込み")
    print("=" * 60)

    try:
        df_master = load_bs_account_master()
        print(f"[OK] BS科目マスタ読み込み成功")
        print(f"  - 科目数: {len(df_master)}科目")
        print(f"  - 列: {list(df_master.columns)}")
        print(f"\n先頭5行:")
        print(df_master.head())
        print(f"\n大分類の種類:")
        print(df_master['大分類'].value_counts())

        # 期待: 29科目
        assert len(df_master) == 29, f"科目数が不正: {len(df_master)} (期待: 29)"
        print(f"\n[OK] 科目数チェック合格: {len(df_master)}科目")

        return True
    except Exception as e:
        print(f"[NG] エラー: {e}")
        return False


def test_available_bs_years():
    """利用可能BS年度取得テスト"""
    print("\n" + "=" * 60)
    print("テスト2: 利用可能BS年度取得")
    print("=" * 60)

    try:
        years = get_available_bs_years()
        print(f"[OK] BS年度取得成功")
        print(f"  - 年度数: {len(years)}年度")
        print(f"  - 年度リスト: {years}")

        # 期待: 10年度（H27-H31, R2-R6）
        assert len(years) == 10, f"年度数が不正: {len(years)} (期待: 10)"

        # ソート確認（H27が最初、R6が最後）
        assert years[0].startswith('H'), f"先頭が平成でない: {years[0]}"
        assert years[-1] == 'R6', f"末尾がR6でない: {years[-1]}"
        print(f"\n[OK] 年度ソートチェック合格: {years[0]} -> {years[-1]}")

        return True
    except Exception as e:
        print(f"[NG] エラー: {e}")
        return False


def test_bs_data_loading():
    """BSデータ読み込みテスト"""
    print("\n" + "=" * 60)
    print("テスト3: BSデータ読み込み")
    print("=" * 60)

    try:
        df = load_bs_monthly_data()
        print(f"[OK] BSデータ読み込み成功")
        print(f"  - 行数: {len(df)}行")
        print(f"  - 列: {list(df.columns)}")
        print(f"\n先頭5行:")
        print(df.head())

        # 列名チェック
        required_columns = ['年度', '科目コード', '科目名称', '4月', '5月', '6月',
                          '7月', '8月', '9月', '10月', '11月', '12月', '1月', '2月', '3月', '年間合計']
        for col in required_columns:
            assert col in df.columns, f"列が不足: {col}"
        print(f"\n[OK] 列名チェック合格")

        # 年度の種類
        years_in_data = sorted(df['年度'].unique().tolist(), key=lambda x: (x.startswith('R'), int(x[1:])))
        print(f"\n年度の種類: {years_in_data}")

        # 科目コード範囲チェック（111-399, 920）
        codes = df['科目コード'].unique()
        invalid_codes = [c for c in codes if not (111 <= c <= 399 or c == 920)]
        assert len(invalid_codes) == 0, f"不正な科目コード: {invalid_codes}"
        print(f"\n[OK] 科目コード範囲チェック合格（111-399, 920）")

        # サンプルデータ確認（現金 111）
        sample = df[(df['科目コード'] == 111) & (df['年度'] == 'R6')]
        if not sample.empty:
            print(f"\nサンプルデータ（現金 111, R6年度）:")
            print(f"  4月: {sample['4月'].values[0]:,.0f}円")
            print(f"  年間合計: {sample['年間合計'].values[0]:,.0f}円")

        return True
    except Exception as e:
        print(f"[NG] エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_year_sort():
    """年度ソートテスト"""
    print("\n" + "=" * 60)
    print("テスト4: 年度ソート機能")
    print("=" * 60)

    test_cases = [
        (['R6', 'H27', 'R5'], ['H27', 'R5', 'R6']),
        (['R2', 'R10', 'H30', 'H29'], ['H29', 'H30', 'R2', 'R10']),
        (['H31', 'R1'], ['H31', 'R1']),
    ]

    all_passed = True
    for input_years, expected in test_cases:
        result = sort_years(input_years)
        if result == expected:
            print(f"[OK] {input_years} -> {result}")
        else:
            print(f"[NG] {input_years} -> {result} (期待: {expected})")
            all_passed = False

    return all_passed


def main():
    """全テスト実行"""
    print("\n" + "=" * 60)
    print("BS機能 単体テスト")
    print("=" * 60)

    results = []

    # テスト実行
    results.append(("BS科目マスタ読み込み", test_bs_account_master()))
    results.append(("利用可能BS年度取得", test_available_bs_years()))
    results.append(("BSデータ読み込み", test_bs_data_loading()))
    results.append(("年度ソート", test_year_sort()))

    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)

    for test_name, result in results:
        status = "[OK] 合格" if result else "[NG] 不合格"
        print(f"{test_name}: {status}")

    total = len(results)
    passed = sum(1 for _, r in results if r)

    print(f"\n合計: {passed}/{total} テスト合格")

    if passed == total:
        print("\n[OK] 全テスト合格！")
        return 0
    else:
        print("\n[NG] 一部テストが失敗しました")
        return 1


if __name__ == "__main__":
    exit(main())
