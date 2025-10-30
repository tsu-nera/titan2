"""
EEG周波数バンド統計モジュール
"""

import numpy as np
import pandas as pd

from .constants import FREQ_BANDS


def calculate_band_statistics(df, bands=None):
    """
    各周波数バンドの基本統計を計算

    Parameters
    ----------
    df : pd.DataFrame
        Mind Monitorデータフレーム（バンドパワー列を含む）
    bands : list, optional
        バンド名のリスト（デフォルト: ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']）

    Returns
    -------
    stats_dict : dict
        {
            'statistics': pd.DataFrame,  # バンド統計テーブル
            'bands': list  # バンド名リスト
        }
    """
    if bands is None:
        bands = list(FREQ_BANDS.keys())

    summary_rows = []

    for band in bands:
        # バンド名で始まるカラムを取得
        cols = [c for c in df.columns if c.startswith(f'{band}_')]
        if not cols:
            continue

        # 数値変換とゼロ値の除外
        numeric = df[cols].apply(pd.to_numeric, errors='coerce')
        numeric = numeric.replace(0.0, np.nan)

        summary_rows.append({
            'バンド': band,
            '平均値': numeric.stack().mean(),
            '標準偏差': numeric.stack().std(),
            '有効データ率 (%)': numeric.notna().stack().mean() * 100,
        })

    return {
        'statistics': pd.DataFrame(summary_rows),
        'bands': bands
    }
