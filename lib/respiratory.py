"""
呼吸数推定ライブラリ
心拍変動（HRV）から呼吸数を推定
"""

import numpy as np
from scipy.fft import fft, fftfreq
from scipy.signal import welch


def estimate_rr_intervals(heart_rate_bpm):
    """
    心拍数(BPM)からRRインターバル(ms)を推定

    Parameters
    ----------
    heart_rate_bpm : array-like
        心拍数データ (beats per minute)

    Returns
    -------
    rr_intervals : np.ndarray
        RRインターバル (milliseconds)
    """
    return 60000.0 / heart_rate_bpm


def estimate_respiratory_rate_welch(rr_intervals, sampling_rate=1.0):
    """
    Welch法を使用してRRインターバルから呼吸数を推定

    Parameters
    ----------
    rr_intervals : array-like
        RRインターバルデータ (milliseconds)
    sampling_rate : float
        サンプリングレート (Hz)

    Returns
    -------
    respiratory_rate : float
        推定された呼吸数 (breaths per minute)
    freqs : np.ndarray
        周波数配列
    psd : np.ndarray
        パワースペクトル密度
    """
    # Welch法でパワースペクトル密度を計算
    freqs, psd = welch(rr_intervals, fs=sampling_rate, nperseg=min(256, len(rr_intervals)))

    # 呼吸域の周波数範囲 (0.15-0.4 Hz = 9-24 breaths/min)
    resp_freq_min = 0.15
    resp_freq_max = 0.4

    mask = (freqs >= resp_freq_min) & (freqs <= resp_freq_max)
    resp_freqs = freqs[mask]
    resp_psd = psd[mask]

    if len(resp_psd) > 0:
        # 最大パワーの周波数を呼吸周波数とする
        peak_idx = np.argmax(resp_psd)
        respiratory_freq = resp_freqs[peak_idx]
        respiratory_rate = respiratory_freq * 60  # Hz to breaths/min
    else:
        respiratory_rate = np.nan

    return respiratory_rate, freqs, psd


def estimate_respiratory_rate_fft(rr_intervals, sampling_rate=1.0, window_size=60):
    """
    FFTを使用してRRインターバルから呼吸数を推定（スライディングウィンドウ）

    Parameters
    ----------
    rr_intervals : array-like
        RRインターバルデータ (milliseconds)
    sampling_rate : float
        サンプリングレート (Hz)
    window_size : int
        解析ウィンドウサイズ (秒)

    Returns
    -------
    respiratory_rates : list
        推定された呼吸数 (breaths per minute)
    timestamps : list
        各推定に対応するタイムスタンプインデックス
    """
    respiratory_rates = []
    timestamps = []

    # ウィンドウサイズをサンプル数に変換
    window_samples = int(window_size * sampling_rate)
    step_size = int(window_samples / 2)  # 50% overlap

    for i in range(0, len(rr_intervals) - window_samples, step_size):
        window_data = rr_intervals[i:i+window_samples]

        # トレンドを除去（平均を引く）
        window_data = window_data - np.mean(window_data)

        # FFTを計算
        n = len(window_data)
        fft_values = fft(window_data)
        fft_freqs = fftfreq(n, 1/sampling_rate)

        # 正の周波数のみを使用
        positive_freqs = fft_freqs[:n//2]
        positive_fft = np.abs(fft_values[:n//2])

        # 呼吸域の周波数範囲 (0.15-0.4 Hz = 9-24 breaths/min)
        resp_freq_min = 0.15
        resp_freq_max = 0.4

        # 呼吸域内のピークを検出
        mask = (positive_freqs >= resp_freq_min) & (positive_freqs <= resp_freq_max)
        resp_freqs = positive_freqs[mask]
        resp_power = positive_fft[mask]

        if len(resp_power) > 0:
            # 最大パワーの周波数を呼吸周波数とする
            peak_idx = np.argmax(resp_power)
            respiratory_freq = resp_freqs[peak_idx]
            respiratory_rate = respiratory_freq * 60  # Hz to breaths/min

            respiratory_rates.append(respiratory_rate)
            timestamps.append(i + window_samples // 2)

    return respiratory_rates, timestamps


def analyze_respiratory(hr_data):
    """
    心拍数データから呼吸数を推定

    Parameters
    ----------
    hr_data : dict
        get_heart_rate_data()の戻り値
        {
            'heart_rate': np.ndarray,
            'time': np.ndarray,
            'timestamps': np.ndarray
        }

    Returns
    -------
    respiratory_results : dict
        {
            'rr_intervals': np.ndarray,
            'respiratory_rate_welch': float,
            'respiratory_rates_fft': list,
            'respiratory_timestamps': list,
            'freqs': np.ndarray,
            'psd': np.ndarray,
            'sampling_rate': float,
            'stats': dict
        }
    """
    heart_rate = hr_data['heart_rate']
    time = hr_data['time']

    # RRインターバルを推定
    rr_intervals = estimate_rr_intervals(heart_rate)

    # サンプリングレートを推定
    # 注: Mind MonitorのCSVは時系列が乱れている場合があるため、
    # 正の時間差のみを使用して推定
    time_diff = np.diff(time)
    positive_diffs = time_diff[time_diff > 0]

    if len(positive_diffs) > 0:
        sampling_rate = 1.0 / np.median(positive_diffs)
    else:
        # フォールバック: Muse S Athenaの仕様値を使用
        # PPG/fNIRS: 64 Hz (仕様値)
        # 注: 実際のデータは異なる場合があるため、推定を優先
        sampling_rate = 64.0

    # Welch法で呼吸数推定
    resp_rate_welch, freqs, psd = estimate_respiratory_rate_welch(
        rr_intervals, sampling_rate
    )

    # FFT法で時系列呼吸数推定
    resp_rates_fft, resp_timestamps = estimate_respiratory_rate_fft(
        rr_intervals, sampling_rate, window_size=60
    )

    # 統計情報
    stats = {
        'rr_mean': np.mean(rr_intervals),
        'rr_std': np.std(rr_intervals),
        'rr_min': np.min(rr_intervals),
        'rr_max': np.max(rr_intervals),
        'respiratory_rate_welch': resp_rate_welch,
        'respiratory_rate_fft_mean': np.mean(resp_rates_fft) if len(resp_rates_fft) > 0 else np.nan,
        'respiratory_rate_fft_std': np.std(resp_rates_fft) if len(resp_rates_fft) > 0 else np.nan,
    }

    return {
        'rr_intervals': rr_intervals,
        'respiratory_rate_welch': resp_rate_welch,
        'respiratory_rates_fft': resp_rates_fft,
        'respiratory_timestamps': resp_timestamps,
        'freqs': freqs,
        'psd': psd,
        'sampling_rate': sampling_rate,
        'stats': stats,
        'time': time
    }
