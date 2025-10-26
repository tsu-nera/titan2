"""
呼吸数推定スクリプト
Mind Monitor (Muse) データから呼吸数を推定

方法:
1. 心拍数データから心拍間隔(RR interval)を算出
2. 呼吸性不整脈(RSA: Respiratory Sinus Arrhythmia)を利用
3. 周波数解析(FFT)でHF帯域(0.15-0.4 Hz)のピークを検出
4. ピーク周波数から呼吸数を推定
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.fft import fft, fftfreq
from scipy.signal import find_peaks, welch
import warnings
warnings.filterwarnings('ignore')

def load_muse_data(csv_path):
    """
    Mind Monitor CSVデータを読み込む

    Parameters:
    -----------
    csv_path : str
        CSVファイルのパス

    Returns:
    --------
    df : pandas.DataFrame
        読み込んだデータフレーム
    """
    print(f"Loading data from: {csv_path}")
    df = pd.read_csv(csv_path)

    # TimeStampをdatetime型に変換
    df['TimeStamp'] = pd.to_datetime(df['TimeStamp'])

    # Heart_Rateが0でないデータのみ抽出
    df_hr = df[df['Heart_Rate'] > 0].copy()

    print(f"Total rows: {len(df)}")
    print(f"Rows with valid heart rate: {len(df_hr)}")
    print(f"Duration: {(df['TimeStamp'].max() - df['TimeStamp'].min()).total_seconds():.1f} seconds")

    return df_hr

def estimate_rr_intervals(heart_rate_bpm):
    """
    心拍数(BPM)からRRインターバル(ms)を推定

    Parameters:
    -----------
    heart_rate_bpm : array-like
        心拍数データ (beats per minute)

    Returns:
    --------
    rr_intervals : np.ndarray
        RRインターバル (milliseconds)
    """
    # RR interval (ms) = 60000 / HR (bpm)
    rr_intervals = 60000.0 / heart_rate_bpm
    return rr_intervals

def estimate_respiratory_rate_fft(rr_intervals, sampling_rate=1.0, window_size=60):
    """
    FFTを使用してRRインターバルから呼吸数を推定

    Parameters:
    -----------
    rr_intervals : array-like
        RRインターバルデータ (milliseconds)
    sampling_rate : float
        サンプリングレート (Hz)
    window_size : int
        解析ウィンドウサイズ (秒)

    Returns:
    --------
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

def estimate_respiratory_rate_welch(rr_intervals, sampling_rate=1.0):
    """
    Welch法を使用してRRインターバルから呼吸数を推定

    Parameters:
    -----------
    rr_intervals : array-like
        RRインターバルデータ (milliseconds)
    sampling_rate : float
        サンプリングレート (Hz)

    Returns:
    --------
    respiratory_rate : float
        推定された呼吸数 (breaths per minute)
    freqs : np.ndarray
        周波数配列
    psd : np.ndarray
        パワースペクトル密度
    """
    # Welch法でパワースペクトル密度を計算
    freqs, psd = welch(rr_intervals, fs=sampling_rate, nperseg=min(256, len(rr_intervals)))

    # 呼吸域の周波数範囲 (0.15-0.4 Hz)
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

def plot_results(df_hr, rr_intervals, resp_rates, resp_timestamps, save_path='respiratory_analysis.png'):
    """
    解析結果を可視化

    Parameters:
    -----------
    df_hr : pandas.DataFrame
        心拍数データフレーム
    rr_intervals : np.ndarray
        RRインターバル
    resp_rates : list
        推定呼吸数
    resp_timestamps : list
        タイムスタンプインデックス
    save_path : str
        保存ファイルパス
    """
    fig, axes = plt.subplots(3, 1, figsize=(15, 12))

    # プロット1: 心拍数
    time_seconds = (df_hr['TimeStamp'] - df_hr['TimeStamp'].iloc[0]).dt.total_seconds()
    axes[0].plot(time_seconds, df_hr['Heart_Rate'], 'b-', alpha=0.7, linewidth=0.5)
    axes[0].set_xlabel('Time (seconds)')
    axes[0].set_ylabel('Heart Rate (BPM)')
    axes[0].set_title('Heart Rate Over Time')
    axes[0].grid(True, alpha=0.3)

    # プロット2: RRインターバル（心拍変動）
    axes[1].plot(time_seconds, rr_intervals, 'g-', alpha=0.7, linewidth=0.5)
    axes[1].set_xlabel('Time (seconds)')
    axes[1].set_ylabel('RR Interval (ms)')
    axes[1].set_title('Heart Rate Variability (RR Intervals)')
    axes[1].grid(True, alpha=0.3)

    # プロット3: 推定呼吸数
    if len(resp_rates) > 0:
        resp_time = time_seconds.iloc[resp_timestamps]
        axes[2].plot(resp_time, resp_rates, 'r-', marker='o', markersize=3, linewidth=1.5)
        axes[2].set_xlabel('Time (seconds)')
        axes[2].set_ylabel('Respiratory Rate (breaths/min)')
        axes[2].set_title(f'Estimated Respiratory Rate (Mean: {np.mean(resp_rates):.1f} ± {np.std(resp_rates):.1f} breaths/min)')
        axes[2].grid(True, alpha=0.3)
        axes[2].set_ylim([0, 30])

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"\nPlot saved to: {save_path}")
    plt.close()

def plot_frequency_spectrum(freqs, psd, save_path='frequency_spectrum.png'):
    """
    周波数スペクトルを可視化

    Parameters:
    -----------
    freqs : np.ndarray
        周波数配列
    psd : np.ndarray
        パワースペクトル密度
    save_path : str
        保存ファイルパス
    """
    fig, ax = plt.subplots(figsize=(12, 6))

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
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"Frequency spectrum saved to: {save_path}")
    plt.close()

def main(csv_path):
    """
    メイン処理
    """
    print("="*60)
    print("Respiratory Rate Estimation from Muse Data")
    print("="*60)

    # データ読み込み
    df_hr = load_muse_data(csv_path)

    if len(df_hr) == 0:
        print("Error: No valid heart rate data found.")
        return

    # RRインターバルを推定
    print("\nEstimating RR intervals from heart rate...")
    rr_intervals = estimate_rr_intervals(df_hr['Heart_Rate'].values)
    print(f"Mean RR interval: {np.mean(rr_intervals):.1f} ms")
    print(f"RR interval variability (std): {np.std(rr_intervals):.1f} ms")

    # サンプリングレートを推定
    time_diff = df_hr['TimeStamp'].diff().dt.total_seconds()
    sampling_rate = 1.0 / time_diff.median()
    print(f"Estimated sampling rate: {sampling_rate:.2f} Hz")

    # 方法1: FFTベースのスライディングウィンドウ解析
    print("\n" + "="*60)
    print("Method 1: FFT-based Sliding Window Analysis")
    print("="*60)
    resp_rates_fft, resp_timestamps = estimate_respiratory_rate_fft(
        rr_intervals,
        sampling_rate=sampling_rate,
        window_size=60
    )

    if len(resp_rates_fft) > 0:
        print(f"Estimated respiratory rate: {np.mean(resp_rates_fft):.1f} ± {np.std(resp_rates_fft):.1f} breaths/min")
        print(f"Range: {np.min(resp_rates_fft):.1f} - {np.max(resp_rates_fft):.1f} breaths/min")

    # 方法2: Welch法（全体データ）
    print("\n" + "="*60)
    print("Method 2: Welch's Method (Overall)")
    print("="*60)
    resp_rate_welch, freqs, psd = estimate_respiratory_rate_welch(
        rr_intervals,
        sampling_rate=sampling_rate
    )
    print(f"Estimated respiratory rate: {resp_rate_welch:.1f} breaths/min")

    # 結果の可視化
    print("\n" + "="*60)
    print("Generating Visualizations")
    print("="*60)
    plot_results(df_hr, rr_intervals, resp_rates_fft, resp_timestamps)
    plot_frequency_spectrum(freqs, psd)

    # サマリー統計
    print("\n" + "="*60)
    print("Summary Statistics")
    print("="*60)
    print(f"Heart Rate: {df_hr['Heart_Rate'].mean():.1f} ± {df_hr['Heart_Rate'].std():.1f} BPM")
    print(f"RR Interval: {np.mean(rr_intervals):.1f} ± {np.std(rr_intervals):.1f} ms")
    if len(resp_rates_fft) > 0:
        print(f"Respiratory Rate (FFT): {np.mean(resp_rates_fft):.1f} ± {np.std(resp_rates_fft):.1f} breaths/min")
    print(f"Respiratory Rate (Welch): {resp_rate_welch:.1f} breaths/min")
    print("="*60)

if __name__ == "__main__":
    # CSVファイルのパス
    csv_path = "/home/tsu-nera/repo/titan2/data/samples/mindMonitor_2025-10-26--08-32-20_1403458594426768660.csv"

    main(csv_path)
