"""
EEG周波数バンド統計モジュール
"""

import numpy as np
import pandas as pd

from .constants import FREQ_BANDS

# HSI品質レベル定義
HSI_QUALITY_LEVELS = {
    1.0: 'Good',
    2.0: 'Medium',
    4.0: 'Bad'
}


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


def calculate_hsi_statistics(df):
    """
    HSI (Horseshoe Signal Index) 接続品質統計を計算

    Parameters
    ----------
    df : pd.DataFrame
        Mind Monitorデータフレーム（HSI_*列を含む）

    Returns
    -------
    hsi_dict : dict
        {
            'statistics': pd.DataFrame,  # チャネル別統計テーブル
            'overall_quality': float,  # 全体品質スコア (1.0=Good, 2.0=Medium, 4.0=Bad)
            'good_ratio': float,  # Good品質の割合 (0.0-1.0)
            'channels': list  # チャネル名リスト
        }
    """
    hsi_cols = [c for c in df.columns if c.startswith('HSI_')]

    if not hsi_cols:
        return {
            'statistics': pd.DataFrame(),
            'overall_quality': None,
            'good_ratio': 0.0,
            'channels': []
        }

    # 数値変換
    hsi_values = df[hsi_cols].apply(pd.to_numeric, errors='coerce')

    # チャネル別統計
    channel_stats = []
    for col in hsi_cols:
        channel_name = col.replace('HSI_', '')
        values = hsi_values[col].dropna()

        if len(values) == 0:
            continue

        # 各品質レベルの割合を計算
        good_ratio = (values == 1.0).mean() * 100
        medium_ratio = (values == 2.0).mean() * 100
        bad_ratio = (values == 4.0).mean() * 100

        # 平均品質（数値が低いほど良い）
        avg_quality = values.mean()

        channel_stats.append({
            'チャネル': channel_name,
            'Good (%)': good_ratio,
            'Medium (%)': medium_ratio,
            'Bad (%)': bad_ratio,
            '平均品質': avg_quality
        })

    stats_df = pd.DataFrame(channel_stats)

    # 全体品質スコア（全チャネルの平均）
    if len(stats_df) > 0:
        overall_quality = stats_df['平均品質'].mean()
        good_ratio = stats_df['Good (%)'].mean() / 100.0
    else:
        overall_quality = None
        good_ratio = 0.0

    return {
        'statistics': stats_df,
        'overall_quality': overall_quality,
        'good_ratio': good_ratio,
        'channels': [col.replace('HSI_', '') for col in hsi_cols]
    }
