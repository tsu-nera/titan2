"""
EEG可視化モジュール
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from .constants import FREQ_BANDS
from .frequency import calculate_psd


def plot_band_power_time_series(
    df,
    bands=None,
    img_path=None,
    rolling_window=50,
    resample_interval='2S',
    smooth_window=5,
    clip_percentile=None
):
    """
    Plot band power time series in Muse App style

    Parameters
    ----------
    df : pd.DataFrame
        Mind Monitor dataframe with band power columns
    bands : list, optional
        List of band names
    img_path : str or Path, optional
        Save path (None to skip saving)
    rolling_window : int
        Window size for moving average
    resample_interval : str, optional
        Resampling interval (e.g., '2S') for smoothing
    smooth_window : int, optional
        Rolling window size (samples) for additional smoothing (centered)
    clip_percentile : float, optional
        Upper percentile threshold to clip extreme spikes (None to disable)

    Returns
    -------
    fig : matplotlib.figure.Figure
        Generated figure object
    """
    if bands is None:
        bands = list(FREQ_BANDS.keys())

    if 'TimeStamp' in df.columns:
        time_values = pd.to_datetime(df['TimeStamp'])
    else:
        time_values = pd.to_datetime(np.arange(len(df)), unit='s')

    band_data = pd.DataFrame(index=time_values)

    for band in bands:
        cols = [c for c in df.columns if c.startswith(f'{band}_')]
        if not cols:
            continue
        numeric = df[cols].apply(pd.to_numeric, errors='coerce')
        band_series = numeric.mean(axis=1)
        band_series = band_series.rolling(window=rolling_window, min_periods=1).mean()
        band_data[band] = band_series.values

    band_data = band_data.sort_index()

    if band_data.empty or band_data.shape[1] == 0:
        raise ValueError('指定したバンドのデータが見つかりません。')

    band_data = band_data.interpolate(method='time').ffill().bfill()

    if resample_interval:
        band_data = band_data.resample(resample_interval).mean().interpolate('time')

    if clip_percentile is not None:
        upper_bounds = band_data.quantile(clip_percentile / 100.0)
        band_data = band_data.clip(upper=upper_bounds, axis=1)

    if smooth_window and smooth_window > 1:
        band_data = band_data.rolling(window=int(smooth_window), min_periods=1, center=True).mean()

    # Muse-style visual settings
    fig, ax = plt.subplots(figsize=(14, 8))

    # Convert time axis to minutes (elapsed time from start)
    if len(band_data.index) == 0:
        raise ValueError('バンドデータの時間軸が空です。')

    elapsed_minutes = (band_data.index - band_data.index[0]).total_seconds() / 60.0

    plot_bands = [band for band in bands if band in band_data.columns]
    color_cycle = plt.get_cmap('tab10')

    for idx, band in enumerate(plot_bands):
        default_color = color_cycle(idx % 10)
        color = FREQ_BANDS.get(band, (None, None, default_color))[2] if band in FREQ_BANDS else default_color
        ax.plot(
            elapsed_minutes,
            band_data[band],
            label=band,
            color=color,
            linewidth=2.5,
            alpha=0.9
        )

    ax.set_xlabel('Time (min)', fontsize=12)

    # Set minute-based tick intervals
    max_minutes = elapsed_minutes.max() if len(elapsed_minutes) else 0
    if max_minutes <= 5:
        tick_interval = 1  # <= 5 min: 1-min intervals
    elif max_minutes <= 15:
        tick_interval = 2  # <= 15 min: 2-min intervals
    else:
        tick_interval = 5  # > 15 min: 5-min intervals

    ticks = np.arange(0, max_minutes + tick_interval, tick_interval) if max_minutes else np.array([0])
    ax.set_xticks(ticks)
    ax.set_xlim(0, max_minutes if max_minutes else 1)

    ax.set_title('Brainwave Powerbands', fontsize=16, fontweight='bold', pad=20)
    ax.set_ylabel('Power (μV²)', fontsize=12)
    ax.legend(loc='upper right', fontsize=11, framealpha=0.8)
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)

    plt.tight_layout()

    if img_path:
        plt.savefig(img_path, dpi=150, bbox_inches='tight')
        plt.close()

    return fig


def plot_psd(psd_dict, bands=None, img_path=None):
    """
    パワースペクトル密度（PSD）をプロット

    Parameters
    ----------
    psd_dict : dict
        calculate_psd()の戻り値
    bands : dict, optional
        バンド定義辞書
    img_path : str or Path, optional
        保存先パス

    Returns
    -------
    fig : matplotlib.figure.Figure
        生成された図オブジェクト
    """
    if bands is None:
        bands = FREQ_BANDS

    freqs = psd_dict['freqs']
    psds = psd_dict['psds']
    channels = psd_dict['channels']

    fig, ax = plt.subplots(figsize=(14, 6))
    channel_colors = ['blue', 'green', 'red', 'purple']

    for ch_name, psd, color in zip(channels, psds, channel_colors):
        channel_label = ch_name.replace('RAW_', '')
        ax.plot(freqs, psd, label=channel_label, linewidth=2, color=color, alpha=0.8)

    # バンド領域をハイライト
    for band, (low, high, color) in bands.items():
        ax.axvspan(low, high, alpha=0.1, color=color, label=f'{band} ({low}-{high}Hz)')

    ax.set_xlim(0, min(50, freqs.max()))
    ax.set_yscale('log')
    ax.set_xlabel('周波数 (Hz)', fontsize=12)
    ax.set_ylabel('パワースペクトル密度 (μV²/Hz)', fontsize=12)
    ax.set_title('脳波のパワースペクトル密度（PSD）', fontsize=14, fontweight='bold')
    ax.grid(True, which='both', alpha=0.3)
    ax.legend(loc='upper right', fontsize=10)
    plt.tight_layout()

    if img_path:
        plt.savefig(img_path, dpi=150, bbox_inches='tight')
        plt.close()

    return fig


def plot_psd_time_series(
    raw,
    channels=None,
    img_path=None,
    fmin=1.0,
    fmax=40.0,
    window_sec=8.0,
    step_sec=2.0,
    clip_percentile=95.0,
    smooth_window=3
):
    """
    PSDの時間推移（滑動Welch法）をプロット

    Parameters
    ----------
    raw : mne.io.Raw
        EEGのRawオブジェクト
    channels : list[str], optional
        プロット対象チャネル（Noneの場合は全チャネル）
    img_path : str or Path, optional
        保存先パス（Noneで保存をスキップ）
    fmin : float
        集計するPSDの最小周波数（Hz）
    fmax : float
        集計するPSDの最大周波数（Hz）
    window_sec : float
        Welch法の窓長（秒）
    step_sec : float
        計算ステップ間隔（秒）
    clip_percentile : float
        外れ値抑制のための上側パーセンタイル（Noneで無効）
    smooth_window : int
        時系列平滑化の窓幅（1で無効）

    Returns
    -------
    fig : matplotlib.figure.Figure
        生成された図オブジェクト
    """

    sfreq = raw.info['sfreq']
    total_duration = raw.times[-1]

    if channels is None:
        channels = raw.ch_names
    else:
        missing = [ch for ch in channels if ch not in raw.ch_names]
        if missing:
            raise ValueError(f'Rawオブジェクトに存在しないチャネル: {missing}')

    window_sec = min(window_sec, total_duration)
    if window_sec <= 0:
        raise ValueError('window_sec が無効です。計測時間より短い値を指定してください。')

    step_sec = max(step_sec, 1.0 / sfreq)

    psd_records = []
    time_points = []

    current_start = 0.0
    picks = channels

    while current_start <= total_duration:
        current_end = min(current_start + window_sec, total_duration)
        if current_end - current_start <= 0:
            break

        segment = raw.copy().pick(picks=picks).crop(
            tmin=current_start,
            tmax=current_end,
            include_tmax=True
        )

        psd_dict = calculate_psd(segment, fmin=fmin, fmax=fmax)
        freqs = psd_dict['freqs']
        band_mask = (freqs >= fmin) & (freqs <= fmax)
        if not np.any(band_mask):
            current_start += step_sec
            continue

        band_psd = psd_dict['psds'][:, band_mask].mean(axis=1)
        psd_records.append(band_psd)

        center_time = current_start + (current_end - current_start) / 2.0
        time_points.append(center_time)

        if current_end >= total_duration:
            break
        current_start += step_sec

    if not psd_records:
        raise ValueError('PSDの計算に失敗しました。周波数範囲や窓長を確認してください。')

    psd_array = np.vstack(psd_records)
    elapsed_minutes = np.array(time_points) / 60.0

    psd_df = pd.DataFrame(psd_array, columns=channels, index=elapsed_minutes)

    if clip_percentile is not None:
        upper_bounds = psd_df.quantile(clip_percentile / 100.0)
        psd_df = psd_df.clip(upper=upper_bounds, axis=1)

    if smooth_window and smooth_window > 1:
        psd_df = psd_df.rolling(window=int(smooth_window), min_periods=1, center=True).median()

    psd_processed = psd_df.to_numpy()
    elapsed_minutes = psd_df.index.to_numpy()

    fig, ax = plt.subplots(figsize=(14, 8))

    color_cycle = plt.get_cmap('tab10')
    channel_labels = [channel.replace('RAW_', '') for channel in channels]

    for idx, channel in enumerate(channel_labels):
        ax.plot(
            elapsed_minutes,
            psd_processed[:, idx],
            label=channel,
            color=color_cycle(idx % 10),
            linewidth=2.5,
            alpha=0.9
        )

    ax.set_xlabel('Time (min)', fontsize=12)
    ax.set_ylabel('PSD (μV²/Hz)', fontsize=12)
    ax.set_title('PSDの時間推移', fontsize=16, fontweight='bold', pad=20)
    ax.legend(loc='upper right', fontsize=11, framealpha=0.8)
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)

    max_minutes = elapsed_minutes.max()
    if max_minutes <= 5:
        tick_interval = 1
    elif max_minutes <= 15:
        tick_interval = 2
    else:
        tick_interval = 5

    ticks = np.arange(0, max_minutes + tick_interval, tick_interval)
    ax.set_xticks(ticks)
    ax.set_xlim(0, max_minutes)

    plt.tight_layout()

    if img_path:
        plt.savefig(img_path, dpi=150, bbox_inches='tight')
        plt.close()

    return fig


def plot_spectrogram(tfr_dict, bands=None, img_path=None):
    """
    スペクトログラムをプロット

    Parameters
    ----------
    tfr_dict : dict
        calculate_spectrogram()の戻り値
    bands : dict, optional
        バンド定義辞書
    img_path : str or Path, optional
        保存先パス

    Returns
    -------
    fig : matplotlib.figure.Figure
        生成された図オブジェクト
    """
    if bands is None:
        bands = FREQ_BANDS

    power = tfr_dict['power']
    freqs = tfr_dict['freqs']
    times = tfr_dict['times']
    channel = tfr_dict['channel']

    # dB変換
    power_db = 10 * np.log10(power)

    fig, ax = plt.subplots(figsize=(14, 7))

    im = ax.pcolormesh(
        times,
        freqs,
        power_db,
        shading='auto',
        cmap='viridis',
        vmin=np.percentile(power_db, 5),
        vmax=np.percentile(power_db, 95)
    )

    # バンド境界線
    fmax = freqs.max()
    for band, (low, high, _) in bands.items():
        if low <= fmax:
            ax.axhline(y=low, color='white', linestyle='--', alpha=0.5, linewidth=1)
            if high <= fmax:
                ax.text(times[-1] * 0.02, (low + high) / 2, band,
                       color='white', fontsize=10, fontweight='bold')

    ax.set_xlabel('時間 (秒)', fontsize=12)
    ax.set_ylabel('周波数 (Hz)', fontsize=12)
    ax.set_title(f'スペクトログラム - {channel.replace("RAW_", "")}',
                fontsize=14, fontweight='bold')
    ax.set_ylim(0, fmax)

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label('パワー (dB, μV²)', fontsize=11)

    plt.tight_layout()

    if img_path:
        plt.savefig(img_path, dpi=150, bbox_inches='tight')
        plt.close()

    return fig


def plot_band_ratios(
    ratios_dict,
    resample_interval='10S',
    img_path=None,
    clip_percentile=95.0,
    smooth_window=5
):
    """
    バンド比率の時系列をプロット

    Parameters
    ----------
    ratios_dict : dict
        calculate_band_ratios()の戻り値
    resample_interval : str
        リサンプリング間隔
    img_path : str or Path, optional
        保存先パス
    clip_percentile : float, optional
        外れ値抑制のための上側パーセンタイル（Noneで無効）
    smooth_window : int, optional
        移動平均の窓サイズ（1で無効）

    Returns
    -------
    fig : matplotlib.figure.Figure
        生成された図オブジェクト
    """
    ratio_df = ratios_dict['ratios'].copy()

    ratio_configs = [
        'リラックス度 (α/β)',
        '集中度 (β/θ)',
        '瞑想深度 (θ/α)',
    ]

    # 外れ値のクリッピング
    if clip_percentile is not None:
        for ratio_name in ratio_configs:
            if ratio_name in ratio_df.columns:
                upper_bound = ratio_df[ratio_name].quantile(clip_percentile / 100.0)
                ratio_df[ratio_name] = ratio_df[ratio_name].clip(upper=upper_bound)

    # 移動平均による平滑化
    if smooth_window and smooth_window > 1:
        for ratio_name in ratio_configs:
            if ratio_name in ratio_df.columns:
                ratio_df[ratio_name] = ratio_df[ratio_name].rolling(
                    window=int(smooth_window),
                    min_periods=1,
                    center=True
                ).median()

    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    colors = ['green', 'orange', 'purple']

    for i, ratio_name in enumerate(ratio_configs):
        if ratio_name in ratio_df.columns:
            # 生データ（薄い色）
            raw_data = ratios_dict['ratios'][ratio_name]
            axes[i].plot(ratios_dict['ratios']['TimeStamp'], raw_data,
                        color=colors[i], linewidth=1, alpha=0.2, label='生データ')

            # 平滑化データ（濃い色）
            axes[i].plot(ratio_df['TimeStamp'], ratio_df[ratio_name],
                        color=colors[i], linewidth=2.5, alpha=0.9, label='移動中央値')

            axes[i].axhline(y=1.0, color='gray', linestyle='--', alpha=0.5, linewidth=1.5,
                           label='基準値 (1.0)')
            axes[i].set_ylabel(ratio_name, fontsize=11, fontweight='bold')
            axes[i].grid(True, alpha=0.3)

            data_values = ratio_df[ratio_name].dropna()
            if len(data_values) > 0:
                y_min = max(0, data_values.quantile(0.05) * 0.9)
                y_max = data_values.quantile(0.95) * 1.1
                axes[i].set_ylim(y_min, y_max)

                mean_val = data_values.mean()
                axes[i].axhline(y=mean_val, color=colors[i], linestyle=':',
                              alpha=0.4, linewidth=1.5, label=f'平均 ({mean_val:.2f})')

            axes[i].legend(loc='upper right', fontsize=9)

    axes[0].set_title(f'脳波指標の時間推移（{resample_interval}ごと平均）',
                     fontsize=14, fontweight='bold')
    axes[-1].set_xlabel('時刻', fontsize=12)
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    fig.autofmt_xdate()
    plt.tight_layout()

    if img_path:
        plt.savefig(img_path, dpi=150, bbox_inches='tight')
        plt.close()

    return fig


def plot_paf(paf_dict, img_path=None):
    """
    Peak Alpha Frequency（PAF）をプロット

    Parameters
    ----------
    paf_dict : dict
        calculate_paf()の戻り値
    img_path : str or Path, optional
        保存先パス

    Returns
    -------
    fig : matplotlib.figure.Figure
        生成された図オブジェクト
    """
    paf_results = paf_dict['paf_by_channel']
    iaf = paf_dict['iaf']
    alpha_low, alpha_high = paf_dict['alpha_range']
    alpha_freqs = paf_dict['alpha_freqs']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    channel_colors = ['blue', 'green', 'red', 'purple']

    # 左図: Alpha帯域のPSDとPAF
    for ch_label, result in paf_results.items():
        color = channel_colors[list(paf_results.keys()).index(ch_label)]
        ax1.plot(alpha_freqs, result['PSD'], label=ch_label,
                linewidth=2, color=color, alpha=0.8)
        ax1.scatter(result['PAF'], result['Power'],
                   s=100, color=color, marker='o', zorder=5)

    ax1.axvline(x=iaf, color='black', linestyle='--', linewidth=2,
               label=f'IAF = {iaf:.2f} Hz')
    ax1.set_xlabel('周波数 (Hz)', fontsize=12)
    ax1.set_ylabel('パワースペクトル密度 (μV²/Hz)', fontsize=12)
    ax1.set_title('Alpha帯域のPSD と PAF', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)

    # 右図: チャネル別PAFの棒グラフ
    channels = list(paf_results.keys())
    pafs = [paf_results[ch]['PAF'] for ch in channels]
    colors_bar = [channel_colors[i] for i in range(len(channels))]

    bars = ax2.bar(channels, pafs, color=colors_bar, alpha=0.7, edgecolor='black')
    ax2.axhline(y=iaf, color='black', linestyle='--', linewidth=2,
               label=f'IAF = {iaf:.2f} Hz')
    ax2.set_ylabel('PAF (Hz)', fontsize=12)
    ax2.set_xlabel('チャネル', fontsize=12)
    ax2.set_title('チャネル別 Peak Alpha Frequency', fontsize=13, fontweight='bold')
    ax2.set_ylim(alpha_low, alpha_high)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3, axis='y')

    for bar, paf in zip(bars, pafs):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{paf:.2f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()

    if img_path:
        plt.savefig(img_path, dpi=150, bbox_inches='tight')
        plt.close()

    return fig


def plot_paf_time_evolution(paf_time_dict, df, paf_dict, img_path=None):
    """
    PAFの時間的変化をプロット

    Parameters
    ----------
    paf_time_dict : dict
        calculate_paf_time_evolution()の戻り値
    df : pd.DataFrame
        タイムスタンプ情報を含むデータフレーム
    paf_dict : dict
        calculate_paf()の戻り値
    img_path : str or Path, optional
        保存先パス

    Returns
    -------
    fig : matplotlib.figure.Figure
        生成された図オブジェクト
    """
    paf_over_time = paf_time_dict['paf_over_time']
    paf_smoothed = paf_time_dict['paf_smoothed']
    times = paf_time_dict['times']
    alpha_power = paf_time_dict['alpha_power']
    alpha_freqs = paf_time_dict['alpha_freqs']

    iaf = paf_dict['iaf']
    alpha_low, alpha_high = paf_dict['alpha_range']

    # 時間軸をタイムスタンプに変換
    start_time = df['TimeStamp'].min()
    time_stamps = [start_time + pd.Timedelta(seconds=t) for t in times]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    # 上図: PAFの時間変化
    ax1.plot(time_stamps, paf_over_time, color='lightblue',
            alpha=0.3, linewidth=1, label='生データ')
    ax1.plot(time_stamps, paf_smoothed, color='blue',
            linewidth=2, label=f'移動平均')
    ax1.axhline(y=iaf, color='red', linestyle='--', linewidth=2,
               label=f'IAF = {iaf:.2f} Hz')
    ax1.fill_between(time_stamps, alpha_low, alpha_high,
                     alpha=0.1, color='green', label='Alpha帯域 (8-13 Hz)')
    ax1.set_ylabel('PAF (Hz)', fontsize=12)
    ax1.set_title('Peak Alpha Frequency の時間推移',
                 fontsize=13, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(alpha_low - 0.5, alpha_high + 0.5)

    # 下図: PAFの変動性（スペクトログラム）
    im = ax2.pcolormesh(
        time_stamps,
        alpha_freqs,
        alpha_power,
        shading='auto',
        cmap='viridis',
        vmin=np.percentile(alpha_power, 5),
        vmax=np.percentile(alpha_power, 95)
    )
    ax2.plot(time_stamps, paf_smoothed, color='red',
            linewidth=2, linestyle='--', label='PAF推移')
    ax2.set_xlabel('時刻', fontsize=12)
    ax2.set_ylabel('周波数 (Hz)', fontsize=12)
    ax2.set_title('Alpha帯域のスペクトログラムとPAF', fontsize=13, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=10)

    cbar = fig.colorbar(im, ax=ax2)
    cbar.set_label('パワー (μV²)', fontsize=11)

    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    fig.autofmt_xdate()

    plt.tight_layout()

    if img_path:
        plt.savefig(img_path, dpi=150, bbox_inches='tight')
        plt.close()

    return fig


def setup_japanese_font():
    """日本語フォント設定"""
    plt.rcParams['font.family'] = 'Noto Sans CJK JP'
    plt.rcParams['axes.unicode_minus'] = False
