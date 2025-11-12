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
        raise ValueError('No data found for specified bands.')

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
        raise ValueError('Band data time axis is empty.')

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


def plot_psd(
    psd_dict,
    bands=None,
    img_path=None,
    use_mne_plot=True,
    spectrum_plot_kwargs=None
):
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
    use_mne_plot : bool
        Trueの場合はmne.Spectrum.plot()をベースにした描画を行い、
        MNE標準のフィルタ境界表示やインタラクションを活用する
    spectrum_plot_kwargs : dict, optional
        mne.Spectrum.plot()へ渡す追加パラメータ

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
    spectrum = psd_dict.get('spectrum')

    axes = []
    fig = None

    def _highlight_bands(ax_list):
        for ax in ax_list:
            for band_name, (low, high, color) in bands.items():
                label = f'{band_name} ({low}-{high}Hz)' if ax is ax_list[0] else None
                ax.axvspan(low, high, alpha=0.12, color=color, label=label)

    def _style_axes(ax_list):
        if not ax_list:
            return
        x_max = min(50.0, freqs.max())
        for ax in ax_list:
            ax.set_xlim(0, x_max)
            ax.set_xlabel('Frequency (Hz)', fontsize=12)
            ax.grid(True, which='both', alpha=0.3)
        primary = ax_list[0]
        primary.set_ylabel('Power Spectral Density (μV²/Hz)', fontsize=12)
        primary.set_title('EEG Power Spectral Density (PSD)', fontsize=14, fontweight='bold')

    def _format_channel_lines(ax):
        if not channels:
            return
        channel_count = len(channels)
        spectral_lines = [
            line for line in ax.lines
            if line.get_linestyle() == '-' and line.get_linewidth() <= 1.0
        ]
        if len(spectral_lines) >= channel_count:
            spectral_lines = spectral_lines[-channel_count:]
        color_cycle = plt.get_cmap('tab10')
        for idx, (line, ch_name) in enumerate(zip(spectral_lines, channels)):
            color = color_cycle(idx % 10)
            line.set_color(color)
            line.set_alpha(0.9)
            line.set_linewidth(2.0)
            line.set_label(ch_name.replace('RAW_', ''))

    used_mne_plot = bool(use_mne_plot and spectrum is not None)

    if used_mne_plot:
        plot_kwargs = {
            'average': False,
            'dB': False,
            'spatial_colors': False,
            'show': False,
        }
        if spectrum_plot_kwargs:
            plot_kwargs.update(spectrum_plot_kwargs)

        fig = spectrum.plot(**plot_kwargs)
        axes = list(fig.axes)
        if axes:
            _format_channel_lines(axes[0])
    else:
        fig, ax = plt.subplots(figsize=(14, 6))
        axes = [ax]
        color_cycle = plt.get_cmap('tab10')
        for idx, (ch_name, psd) in enumerate(zip(channels, psds)):
            channel_label = ch_name.replace('RAW_', '')
            color = color_cycle(idx % 10)
            ax.plot(freqs, psd, label=channel_label, linewidth=2, color=color, alpha=0.85)
        ax.set_yscale('log')

    _highlight_bands(axes)
    _style_axes(axes)

    primary_ax = axes[0] if axes else None
    if primary_ax:
        handles, labels = primary_ax.get_legend_handles_labels()
        if handles:
            primary_ax.legend(loc='upper right', fontsize=10)

    plt.tight_layout()

    if img_path:
        fig.savefig(img_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

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
            raise ValueError(f'Channels not found in Raw object: {missing}')

    window_sec = min(window_sec, total_duration)
    if window_sec <= 0:
        raise ValueError('Invalid window_sec. Please specify a value shorter than the measurement duration.')

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
    ax.set_title('PSD Time Series', fontsize=16, fontweight='bold', pad=20)
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

    ax.set_xlabel('Time (seconds)', fontsize=12)
    ax.set_ylabel('Frequency (Hz)', fontsize=12)
    ax.set_title(f'Spectrogram - {channel.replace("RAW_", "")}',
                fontsize=14, fontweight='bold')
    ax.set_ylim(0, fmax)

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label('Power (dB, μV²)', fontsize=11)

    plt.tight_layout()

    if img_path:
        plt.savefig(img_path, dpi=150, bbox_inches='tight')
        plt.close()

    return fig


def plot_spectrogram_grid(tfr_results, bands=None, img_path=None):
    """
    全チャネルのスペクトログラムを2x2グリッドでプロット

    Parameters
    ----------
    tfr_results : dict
        calculate_spectrogram_all_channels()の戻り値
        {'RAW_TP9': tfr_dict, 'RAW_AF7': tfr_dict, ...}
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

    # 2x2グリッドレイアウト（前頭部上、側頭部下）
    channel_layout = [
        ['RAW_AF7', 'RAW_AF8'],  # 前頭部
        ['RAW_TP9', 'RAW_TP10']  # 側頭部
    ]

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))

    # 全チャネルの最小・最大値を取得（カラースケール統一のため）
    all_powers_db = []
    for tfr_dict in tfr_results.values():
        power_db = 10 * np.log10(tfr_dict['power'])
        all_powers_db.append(power_db)

    if all_powers_db:
        vmin = np.percentile(np.concatenate([p.flatten() for p in all_powers_db]), 5)
        vmax = np.percentile(np.concatenate([p.flatten() for p in all_powers_db]), 95)
    else:
        vmin, vmax = None, None

    for i in range(2):
        for j in range(2):
            channel = channel_layout[i][j]
            ax = axes[i, j]

            if channel in tfr_results:
                tfr_dict = tfr_results[channel]
                power = tfr_dict['power']
                freqs = tfr_dict['freqs']
                times = tfr_dict['times']

                # 秒を分に変換
                times_min = times / 60.0

                # dB変換
                power_db = 10 * np.log10(power)

                # スペクトログラム描画
                im = ax.pcolormesh(
                    times_min,
                    freqs,
                    power_db,
                    shading='auto',
                    cmap='viridis',
                    vmin=vmin,
                    vmax=vmax
                )

                # バンド境界線
                fmax = freqs.max()
                for band, (low, high, _) in bands.items():
                    if low <= fmax:
                        ax.axhline(y=low, color='white', linestyle='--', alpha=0.5, linewidth=0.8)
                        if high <= fmax:
                            ax.text(times_min[-1] * 0.02, (low + high) / 2, band,
                                   color='white', fontsize=9, fontweight='bold')

                ax.set_xlabel('Time (min)', fontsize=11)
                ax.set_ylabel('Frequency (Hz)', fontsize=11)
                ax.set_title(f'{channel.replace("RAW_", "")}',
                            fontsize=12, fontweight='bold')
                ax.set_ylim(0, fmax)

                # カラーバー（各サブプロットに）
                cbar = fig.colorbar(im, ax=ax)
                cbar.set_label('Power (dB)', fontsize=9)

            else:
                ax.text(0.5, 0.5, f'{channel}\nNo Data',
                       ha='center', va='center', fontsize=12)
                ax.axis('off')

    plt.suptitle('Spectrogram - All Channels', fontsize=14, fontweight='bold', y=0.995)
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
        ('Alpha/Beta', 'リラックス度 (α/β)'),
        ('Beta/Theta', '集中度 (β/θ)'),
        ('Theta/Alpha', '瞑想深度 (θ/α)'),
    ]

    # 外れ値のクリッピング
    if clip_percentile is not None:
        for ratio_key, _ in ratio_configs:
            if ratio_key in ratio_df.columns:
                upper_bound = ratio_df[ratio_key].quantile(clip_percentile / 100.0)
                ratio_df[ratio_key] = ratio_df[ratio_key].clip(upper=upper_bound)

    # 移動平均による平滑化
    if smooth_window and smooth_window > 1:
        for ratio_key, _ in ratio_configs:
            if ratio_key in ratio_df.columns:
                ratio_df[ratio_key] = ratio_df[ratio_key].rolling(
                    window=int(smooth_window),
                    min_periods=1,
                    center=True
                ).median()

    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    colors = ['green', 'orange', 'purple']

    for i, (ratio_key, display_name) in enumerate(ratio_configs):
        if ratio_key in ratio_df.columns:
            # Raw data (light color)
            raw_data = ratios_dict['ratios'][ratio_key]
            axes[i].plot(ratios_dict['ratios']['TimeStamp'], raw_data,
                        color=colors[i], linewidth=1, alpha=0.2, label='Raw Data')

            # Smoothed data (dark color)
            axes[i].plot(ratio_df['TimeStamp'], ratio_df[ratio_key],
                        color=colors[i], linewidth=2.5, alpha=0.9, label='Rolling Median')

            axes[i].axhline(y=1.0, color='gray', linestyle='--', alpha=0.5, linewidth=1.5,
                           label='Baseline (1.0)')
            axes[i].set_ylabel(display_name, fontsize=11, fontweight='bold')
            axes[i].grid(True, alpha=0.3)

            data_values = ratio_df[ratio_key].dropna()
            if len(data_values) > 0:
                y_min = max(0, data_values.quantile(0.05) * 0.9)
                y_max = data_values.quantile(0.95) * 1.1
                axes[i].set_ylim(y_min, y_max)

                mean_val = data_values.mean()
                axes[i].axhline(y=mean_val, color=colors[i], linestyle=':',
                              alpha=0.4, linewidth=1.5, label=f'Mean ({mean_val:.2f})')

            axes[i].legend(loc='upper right', fontsize=9)

    axes[0].set_title(f'EEG Metrics Time Series (averaged every {resample_interval})',
                     fontsize=14, fontweight='bold')
    axes[-1].set_xlabel('Time', fontsize=12)
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
    ax1.set_xlabel('Frequency (Hz)', fontsize=12)
    ax1.set_ylabel('Power Spectral Density (μV²/Hz)', fontsize=12)
    ax1.set_title('Alpha Band PSD and PAF', fontsize=13, fontweight='bold')
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
    ax2.set_xlabel('Channel', fontsize=12)
    ax2.set_title('Peak Alpha Frequency by Channel', fontsize=13, fontweight='bold')
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
            alpha=0.3, linewidth=1, label='Raw Data')
    ax1.plot(time_stamps, paf_smoothed, color='blue',
            linewidth=2, label=f'Rolling Average')
    ax1.axhline(y=iaf, color='red', linestyle='--', linewidth=2,
               label=f'IAF = {iaf:.2f} Hz')
    ax1.fill_between(time_stamps, alpha_low, alpha_high,
                     alpha=0.1, color='green', label='Alpha Band (8-13 Hz)')
    ax1.set_ylabel('PAF (Hz)', fontsize=12)
    ax1.set_title('Peak Alpha Frequency Time Evolution',
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
            linewidth=2, linestyle='--', label='PAF Evolution')
    ax2.set_xlabel('Time', fontsize=12)
    ax2.set_ylabel('Frequency (Hz)', fontsize=12)
    ax2.set_title('Alpha Band Spectrogram and PAF', fontsize=13, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=10)

    cbar = fig.colorbar(im, ax=ax2)
    cbar.set_label('Power (μV²)', fontsize=11)

    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    fig.autofmt_xdate()

    plt.tight_layout()

    if img_path:
        plt.savefig(img_path, dpi=150, bbox_inches='tight')
        plt.close()

    return fig
