"""
Peak Alpha Frequency (PAF) 解析モジュール
"""

import numpy as np
import pandas as pd


def calculate_paf(psd_dict, alpha_range=(8.0, 13.0)):
    """
    Peak Alpha Frequency（PAF）を計算

    Parameters
    ----------
    psd_dict : dict
        calculate_psd()の戻り値
    alpha_range : tuple
        Alpha帯域の範囲（Hz）

    Returns
    -------
    paf_dict : dict
        {
            'paf_by_channel': dict,  # チャネル別PAF {channel: {'PAF': float, 'Power': float, 'PSD': array}}
            'iaf': float,            # Individual Alpha Frequency
            'iaf_std': float,        # IAFの標準偏差
            'alpha_range': tuple     # Alpha帯域範囲
        }
    """
    freqs = psd_dict['freqs']
    psds = psd_dict['psds']
    channels = psd_dict['channels']

    alpha_low, alpha_high = alpha_range
    alpha_mask = (freqs >= alpha_low) & (freqs <= alpha_high)
    alpha_freqs = freqs[alpha_mask]

    paf_results = {}

    for i, ch_name in enumerate(channels):
        ch_label = ch_name.replace('RAW_', '')
        alpha_psd = psds[i][alpha_mask]

        peak_idx = alpha_psd.argmax()
        paf = alpha_freqs[peak_idx]
        peak_power = alpha_psd[peak_idx]

        paf_results[ch_label] = {
            'PAF': paf,
            'Power': peak_power,
            'PSD': alpha_psd,
        }

    # Individual Alpha Frequency（IAF）
    all_pafs = [v['PAF'] for v in paf_results.values()]
    iaf = np.mean(all_pafs)
    iaf_std = np.std(all_pafs)

    return {
        'paf_by_channel': paf_results,
        'iaf': iaf,
        'iaf_std': iaf_std,
        'alpha_range': alpha_range,
        'alpha_freqs': alpha_freqs
    }


def calculate_paf_time_evolution(tfr_dict, paf_dict, window_size=100):
    """
    PAFの時間的変化を計算

    Parameters
    ----------
    tfr_dict : dict
        calculate_spectrogram()の戻り値
    paf_dict : dict
        calculate_paf()の戻り値
    window_size : int
        移動平均のウィンドウサイズ

    Returns
    -------
    paf_time_dict : dict
        {
            'paf_over_time': np.ndarray,     # 各時点のPAF
            'paf_smoothed': np.ndarray,      # スムージング後のPAF
            'times': np.ndarray,             # 時間配列
            'alpha_power': np.ndarray,       # Alpha帯域のパワー
            'alpha_freqs': np.ndarray,       # Alpha帯域の周波数
            'stats': dict                    # 統計情報
        }
    """
    power = tfr_dict['power']
    freqs = tfr_dict['freqs']
    times = tfr_dict['times']

    alpha_low, alpha_high = paf_dict['alpha_range']

    # Alpha帯域のマスク
    alpha_mask = (freqs >= alpha_low) & (freqs <= alpha_high)
    alpha_freqs = freqs[alpha_mask]
    alpha_power = power[alpha_mask, :]

    # 各時間点でのPAFを計算
    paf_over_time = []
    for t_idx in range(alpha_power.shape[1]):
        power_at_t = alpha_power[:, t_idx]
        peak_idx = power_at_t.argmax()
        paf_at_t = alpha_freqs[peak_idx]
        paf_over_time.append(paf_at_t)

    paf_over_time = np.array(paf_over_time)

    # 移動平均でスムージング
    paf_smoothed = pd.Series(paf_over_time).rolling(
        window=window_size, min_periods=1, center=True
    ).mean().values

    # 統計情報
    paf_stats = {
        '平均PAF (Hz)': np.mean(paf_over_time),
        '中央値 (Hz)': np.median(paf_over_time),
        '標準偏差 (Hz)': np.std(paf_over_time),
        '最小値 (Hz)': np.min(paf_over_time),
        '最大値 (Hz)': np.max(paf_over_time),
        '変動係数 (%)': (np.std(paf_over_time) / np.mean(paf_over_time) * 100)
    }

    return {
        'paf_over_time': paf_over_time,
        'paf_smoothed': paf_smoothed,
        'times': times,
        'alpha_power': alpha_power,
        'alpha_freqs': alpha_freqs,
        'stats': paf_stats
    }
