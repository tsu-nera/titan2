"""
EEGバンド比率計算モジュール（リラックス度、集中度、瞑想深度）
"""

import numpy as np
import pandas as pd
from scipy import stats

from .constants import FREQ_BANDS


def calculate_band_ratios(df, resample_interval='10S', bands=None):
    """
    バンド比率を計算（リラックス度、集中度、瞑想深度）

    Parameters
    ----------
    df : pd.DataFrame
        Mind Monitorデータフレーム（バンドパワー列を含む）
    resample_interval : str
        リサンプリング間隔（例: '10S'）
    bands : dict, optional
        バンド定義辞書（デフォルト: FREQ_BANDS）

    Returns
    -------
    ratios_dict : dict
        {
            'ratios': pd.DataFrame,  # 比率の時系列データ（リサンプル済み）
            'statistics': pd.DataFrame,  # 統計サマリー
            'spike_analysis': pd.DataFrame  # スパイク分析
        }
    """
    if bands is None:
        bands = FREQ_BANDS

    ratio_df = pd.DataFrame({'TimeStamp': df['TimeStamp']})

    ratio_configs = [
        ('リラックス度 (α/β)', 'Alpha', 'Beta'),
        ('集中度 (β/θ)', 'Beta', 'Theta'),
        ('瞑想深度 (θ/α)', 'Theta', 'Alpha'),
    ]

    # 各比率を計算
    for ratio_name, num_band, den_band in ratio_configs:
        ratios = []
        for col in [c for c in df.columns if c.startswith(f'{num_band}_')]:
            electrode = col.split('_', 1)[1]
            den_col = f'{den_band}_{electrode}'
            if den_col in df.columns:
                num_vals = pd.to_numeric(df[col], errors='coerce').abs()
                den_vals = pd.to_numeric(df[den_col], errors='coerce').abs()
                den_vals = den_vals.replace(0, np.nan)

                ratio = (num_vals / den_vals).replace([np.inf, -np.inf], np.nan)
                ratios.append(ratio)

        if ratios:
            ratio_df[ratio_name] = pd.concat(ratios, axis=1).mean(axis=1)

    # リサンプリング
    ratio_df_resampled = ratio_df.set_index('TimeStamp').resample(resample_interval).mean().reset_index()

    # 統計サマリー
    summary_scores = []
    for ratio_name, _, _ in ratio_configs:
        if ratio_name in ratio_df.columns:
            values = ratio_df[ratio_name].dropna()
            summary_scores.append({
                '指標': ratio_name,
                '平均値': values.mean(),
                '中央値': values.median(),
                '標準偏差': values.std(),
                '最小値': values.min(),
                '最大値': values.max(),
            })

    # スパイク分析
    spike_info = []
    for ratio_name, _, _ in ratio_configs:
        if ratio_name in ratio_df_resampled.columns:
            values = ratio_df_resampled[ratio_name].dropna()

            if len(values) > 0:
                z_scores = np.abs(stats.zscore(values))
                outliers = values[z_scores > 3]
                cv = (values.std() / values.mean()) * 100

                spike_info.append({
                    '指標': ratio_name,
                    '外れ値数': len(outliers),
                    '外れ値割合 (%)': len(outliers) / len(values) * 100,
                    '変動係数 (%)': cv
                })

    return {
        'ratios': ratio_df_resampled,
        'statistics': pd.DataFrame(summary_scores),
        'spike_analysis': pd.DataFrame(spike_info)
    }
