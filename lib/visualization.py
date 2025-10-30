"""
可視化ライブラリ
Mind Monitor解析結果の統合可視化
"""

import matplotlib.pyplot as plt
import numpy as np


def plot_fnirs(fnirs_results, figsize=(14, 10)):
    """
    fNIRS時系列データを4つのサブプロットで可視化

    Parameters
    ----------
    fnirs_results : dict
        analyze_fnirs()の戻り値
    figsize : tuple
        図のサイズ

    Returns
    -------
    fig : matplotlib.figure.Figure
    axes : np.ndarray
    """
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    fig.suptitle('fNIRS Analysis: HbO/HbR Concentration Changes', fontsize=16, fontweight='bold')

    time = fnirs_results['time']
    left_hbo = fnirs_results['left_hbo']
    left_hbr = fnirs_results['left_hbr']
    right_hbo = fnirs_results['right_hbo']
    right_hbr = fnirs_results['right_hbr']

    # Left HbO
    axes[0, 0].plot(time, left_hbo, color='red', linewidth=1.5)
    axes[0, 0].set_title('Left Hemisphere - HbO (Oxygenated)', fontsize=12, fontweight='bold')
    axes[0, 0].set_xlabel('Time (seconds)')
    axes[0, 0].set_ylabel('Δ[HbO] (µM)')
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].axhline(y=0, color='black', linestyle='--', linewidth=0.8, alpha=0.5)

    # Left HbR
    axes[1, 0].plot(time, left_hbr, color='blue', linewidth=1.5)
    axes[1, 0].set_title('Left Hemisphere - HbR (Deoxygenated)', fontsize=12, fontweight='bold')
    axes[1, 0].set_xlabel('Time (seconds)')
    axes[1, 0].set_ylabel('Δ[HbR] (µM)')
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].axhline(y=0, color='black', linestyle='--', linewidth=0.8, alpha=0.5)

    # Right HbO
    axes[0, 1].plot(time, right_hbo, color='red', linewidth=1.5)
    axes[0, 1].set_title('Right Hemisphere - HbO (Oxygenated)', fontsize=12, fontweight='bold')
    axes[0, 1].set_xlabel('Time (seconds)')
    axes[0, 1].set_ylabel('Δ[HbO] (µM)')
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].axhline(y=0, color='black', linestyle='--', linewidth=0.8, alpha=0.5)

    # Right HbR
    axes[1, 1].plot(time, right_hbr, color='blue', linewidth=1.5)
    axes[1, 1].set_title('Right Hemisphere - HbR (Deoxygenated)', fontsize=12, fontweight='bold')
    axes[1, 1].set_xlabel('Time (seconds)')
    axes[1, 1].set_ylabel('Δ[HbR] (µM)')
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].axhline(y=0, color='black', linestyle='--', linewidth=0.8, alpha=0.5)

    plt.tight_layout()
    return fig, axes


def plot_fnirs_muse_style(fnirs_results, figsize=(14, 8)):
    """
    fNIRS時系列データをMuse App風に可視化
    4つの折れ線を重ねて表示（Left HbR, Right HbR, Left HbO, Right HbO）

    Parameters
    ----------
    fnirs_results : dict
        analyze_fnirs()の戻り値
    figsize : tuple
        図のサイズ

    Returns
    -------
    fig : matplotlib.figure.Figure
    ax : matplotlib.axes.Axes
    """
    fig, ax = plt.subplots(figsize=figsize)

    # 時間を分単位に変換
    time_min = fnirs_results['time'] / 60.0

    left_hbo = fnirs_results['left_hbo']
    left_hbr = fnirs_results['left_hbr']
    right_hbo = fnirs_results['right_hbo']
    right_hbr = fnirs_results['right_hbr']

    # Muse App風のカラー設定
    # HbO: 赤/オレンジ系、HbR: 青系
    ax.plot(time_min, left_hbr, color='#3B82F6', linewidth=1.2, label='Left HbR', alpha=0.9)
    ax.plot(time_min, right_hbr, color='#60A5FA', linewidth=1.2, label='Right HbR', alpha=0.9)
    ax.plot(time_min, left_hbo, color='#EF4444', linewidth=1.2, label='Left HbO', alpha=0.9)
    ax.plot(time_min, right_hbo, color='#F97316', linewidth=1.2, label='Right HbO', alpha=0.9)

    # 0ラインを追加
    ax.axhline(y=0, color='gray', linestyle='--', linewidth=1.0, alpha=0.5)

    # グリッド
    ax.grid(True, alpha=0.2, linestyle='-', linewidth=0.5)

    # ラベルとタイトル
    ax.set_xlabel('Time (minutes)', fontsize=12)
    ax.set_ylabel('Concentration Change (µM)', fontsize=12)
    ax.set_title('Brain Oxygenation (Muse App Style)', fontsize=14, fontweight='bold')

    # 凡例
    ax.legend(loc='upper right', framealpha=0.9, fontsize=10)

    # Y軸の範囲を適切に設定
    all_values = np.concatenate([left_hbo, left_hbr, right_hbo, right_hbr])
    y_min = np.floor(np.min(all_values))
    y_max = np.ceil(np.max(all_values))
    ax.set_ylim([y_min, y_max])

    plt.tight_layout()
    return fig, ax


def plot_respiratory(hr_data, respiratory_results, figsize=(15, 12)):
    """
    心拍数・HRV・呼吸数の時系列データを可視化

    Parameters
    ----------
    hr_data : dict
        get_heart_rate_data()の戻り値
    respiratory_results : dict
        analyze_respiratory()の戻り値
    figsize : tuple
        図のサイズ

    Returns
    -------
    fig : matplotlib.figure.Figure
    axes : np.ndarray
    """
    fig, axes = plt.subplots(3, 1, figsize=figsize)
    fig.suptitle('Respiratory Rate Estimation', fontsize=16, fontweight='bold')

    time = respiratory_results['time']
    heart_rate = hr_data['heart_rate']
    rr_intervals = respiratory_results['rr_intervals']
    resp_rates = respiratory_results['respiratory_rates_fft']
    resp_timestamps = respiratory_results['respiratory_timestamps']

    # プロット1: 心拍数
    axes[0].plot(time, heart_rate, 'b-', alpha=0.7, linewidth=0.5)
    axes[0].set_xlabel('Time (seconds)')
    axes[0].set_ylabel('Heart Rate (BPM)')
    axes[0].set_title('Heart Rate Over Time')
    axes[0].grid(True, alpha=0.3)

    # プロット2: RRインターバル（心拍変動）
    axes[1].plot(time, rr_intervals, 'g-', alpha=0.7, linewidth=0.5)
    axes[1].set_xlabel('Time (seconds)')
    axes[1].set_ylabel('RR Interval (ms)')
    axes[1].set_title('Heart Rate Variability (RR Intervals)')
    axes[1].grid(True, alpha=0.3)

    # プロット3: 推定呼吸数
    if len(resp_rates) > 0:
        resp_time = time[resp_timestamps]
        axes[2].plot(resp_time, resp_rates, 'r-', marker='o', markersize=3, linewidth=1.5)
        axes[2].set_xlabel('Time (seconds)')
        axes[2].set_ylabel('Respiratory Rate (breaths/min)')
        axes[2].set_title(f'Estimated Respiratory Rate (Mean: {np.mean(resp_rates):.1f} ± {np.std(resp_rates):.1f} breaths/min)')
        axes[2].grid(True, alpha=0.3)
        axes[2].set_ylim([0, 30])

    plt.tight_layout()
    return fig, axes


def plot_frequency_spectrum(respiratory_results, figsize=(12, 6)):
    """
    周波数スペクトルを可視化

    Parameters
    ----------
    respiratory_results : dict
        analyze_respiratory()の戻り値
    figsize : tuple
        図のサイズ

    Returns
    -------
    fig : matplotlib.figure.Figure
    ax : matplotlib.axes.Axes
    """
    fig, ax = plt.subplots(figsize=figsize)

    freqs = respiratory_results['freqs']
    psd = respiratory_results['psd']

    ax.plot(freqs, psd, 'b-', linewidth=1.5)
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Power Spectral Density')
    ax.set_title('Heart Rate Variability - Frequency Spectrum')
    ax.grid(True, alpha=0.3)

    # 呼吸域をハイライト
    ax.axvspan(0.15, 0.4, alpha=0.3, color='red', label='Respiratory Range (0.15-0.4 Hz)')
    ax.legend()
    ax.set_xlim([0, 0.5])

    plt.tight_layout()
    return fig, ax


def plot_integrated_dashboard(fnirs_results, hr_data, respiratory_results, figsize=(18, 12)):
    """
    fNIRS、心拍数、呼吸数を統合したダッシュボード

    Parameters
    ----------
    fnirs_results : dict
        analyze_fnirs()の戻り値
    hr_data : dict
        get_heart_rate_data()の戻り値
    respiratory_results : dict
        analyze_respiratory()の戻り値
    figsize : tuple
        図のサイズ

    Returns
    -------
    fig : matplotlib.figure.Figure
    axes : np.ndarray
    """
    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

    # Row 1: fNIRS HbO (Left & Right)
    ax_left_hbo = fig.add_subplot(gs[0, 0])
    ax_right_hbo = fig.add_subplot(gs[0, 1])

    time_fnirs = fnirs_results['time']
    ax_left_hbo.plot(time_fnirs, fnirs_results['left_hbo'], 'r-', linewidth=1.0)
    ax_left_hbo.set_title('Left Hemisphere - HbO', fontweight='bold')
    ax_left_hbo.set_ylabel('Δ[HbO] (µM)')
    ax_left_hbo.grid(True, alpha=0.3)
    ax_left_hbo.axhline(y=0, color='black', linestyle='--', linewidth=0.5, alpha=0.5)

    ax_right_hbo.plot(time_fnirs, fnirs_results['right_hbo'], 'r-', linewidth=1.0)
    ax_right_hbo.set_title('Right Hemisphere - HbO', fontweight='bold')
    ax_right_hbo.set_ylabel('Δ[HbO] (µM)')
    ax_right_hbo.grid(True, alpha=0.3)
    ax_right_hbo.axhline(y=0, color='black', linestyle='--', linewidth=0.5, alpha=0.5)

    # Row 2: fNIRS HbR (Left & Right)
    ax_left_hbr = fig.add_subplot(gs[1, 0])
    ax_right_hbr = fig.add_subplot(gs[1, 1])

    ax_left_hbr.plot(time_fnirs, fnirs_results['left_hbr'], 'b-', linewidth=1.0)
    ax_left_hbr.set_title('Left Hemisphere - HbR', fontweight='bold')
    ax_left_hbr.set_ylabel('Δ[HbR] (µM)')
    ax_left_hbr.grid(True, alpha=0.3)
    ax_left_hbr.axhline(y=0, color='black', linestyle='--', linewidth=0.5, alpha=0.5)

    ax_right_hbr.plot(time_fnirs, fnirs_results['right_hbr'], 'b-', linewidth=1.0)
    ax_right_hbr.set_title('Right Hemisphere - HbR', fontweight='bold')
    ax_right_hbr.set_ylabel('Δ[HbR] (µM)')
    ax_right_hbr.grid(True, alpha=0.3)
    ax_right_hbr.axhline(y=0, color='black', linestyle='--', linewidth=0.5, alpha=0.5)

    # Row 3: Heart Rate & Respiratory Rate
    ax_hr = fig.add_subplot(gs[2, 0])
    ax_resp = fig.add_subplot(gs[2, 1])

    time_hr = respiratory_results['time']
    ax_hr.plot(time_hr, hr_data['heart_rate'], 'g-', linewidth=0.8, alpha=0.7)
    ax_hr.set_title('Heart Rate', fontweight='bold')
    ax_hr.set_xlabel('Time (seconds)')
    ax_hr.set_ylabel('Heart Rate (BPM)')
    ax_hr.grid(True, alpha=0.3)

    resp_rates = respiratory_results['respiratory_rates_fft']
    resp_timestamps = respiratory_results['respiratory_timestamps']
    if len(resp_rates) > 0:
        resp_time = time_hr[resp_timestamps]
        ax_resp.plot(resp_time, resp_rates, 'r-', marker='o', markersize=2, linewidth=1.0)
        ax_resp.set_title(f'Respiratory Rate (Mean: {np.mean(resp_rates):.1f} bpm)', fontweight='bold')
        ax_resp.set_xlabel('Time (seconds)')
        ax_resp.set_ylabel('Respiratory Rate (breaths/min)')
        ax_resp.grid(True, alpha=0.3)
        ax_resp.set_ylim([0, 30])

    fig.suptitle('Integrated Physiological Monitoring Dashboard', fontsize=18, fontweight='bold', y=0.995)
    return fig, gs
