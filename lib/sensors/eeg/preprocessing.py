"""
EEGデータの前処理（MNE RawArray準備）
"""

import warnings
import pandas as pd
import mne

from .constants import DEFAULT_SFREQ

# Warningsとログを抑制
warnings.filterwarnings('ignore')
mne.set_log_level('ERROR')


def filter_signal_quality(df, require_headband=True, require_all_good=True):
    """HeadBandOn/HSIの品質に基づいてデータをフィルタ"""

    quality_mask = pd.Series(True, index=df.index)

    if require_headband and 'HeadBandOn' in df.columns:
        headband_on = pd.to_numeric(df['HeadBandOn'], errors='coerce') == 1
        quality_mask &= headband_on.fillna(False)

    hsi_cols = [c for c in df.columns if c.startswith('HSI_')]
    if hsi_cols:
        hsi_values = df[hsi_cols].apply(pd.to_numeric, errors='coerce')
        if require_all_good:
            quality_mask &= hsi_values.eq(1).all(axis=1)
        else:
            quality_mask &= hsi_values.le(2).all(axis=1)

    if quality_mask.any():
        filtered = df.loc[quality_mask].copy()
        if filtered.empty:
            filtered = df.copy()
    else:
        filtered = df.copy()

    return filtered, quality_mask


def prepare_mne_raw(df, sfreq=None):
    """
    MNE RawArrayの準備

    Parameters
    ----------
    df : pd.DataFrame
        Mind Monitorデータフレーム（RAW_*列を含む）
    sfreq : float, optional
        サンプリングレート（Noneの場合は自動推定）

    Returns
    -------
    mne_dict : dict or None
        {
            'raw': mne.io.RawArray,
            'channels': list,
            'sfreq': float,
            'n_samples': int
        }
        RAWチャネルが見つからない場合はNone
    """
    raw_cols = [c for c in df.columns if c.startswith('RAW_')]
    if not raw_cols:
        return None

    df_filtered, _ = filter_signal_quality(df)

    # 数値変換と前処理
    numeric = df_filtered[raw_cols].apply(pd.to_numeric, errors='coerce')
    frame = pd.concat([df_filtered['TimeStamp'], numeric], axis=1)
    frame = frame.set_index('TimeStamp')

    # 重複タイムスタンプは平均化
    frame = frame.groupby(level=0).mean()

    # 時間補間で欠損値を埋める
    frame = frame.interpolate(method='time').ffill().bfill()

    # サンプリングレートの推定
    if sfreq is None:
        diffs = frame.index.to_series().diff().dropna()
        dt_seconds = diffs.median().total_seconds()
        sfreq = 1.0 / dt_seconds if dt_seconds > 0 else DEFAULT_SFREQ

    # MNE RawArrayの作成
    ch_names = list(frame.columns)
    ch_types = ['eeg'] * len(ch_names)
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types)

    # μVスケールをVに変換
    data = frame.to_numpy().T * 1e-6

    raw = mne.io.RawArray(data, info, copy='auto', verbose=False)

    # DCドリフト軽減のためのハイパスフィルタ
    if sfreq > 2.0:
        raw = raw.filter(l_freq=1.0, h_freq=None, fir_design='firwin', verbose=False)

    return {
        'raw': raw,
        'channels': ch_names,
        'sfreq': sfreq,
        'n_samples': len(frame)
    }
