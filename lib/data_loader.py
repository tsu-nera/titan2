"""
Mind Monitor データローダー
CSV読み込みと前処理の共通関数
"""

import pandas as pd
import numpy as np
from pathlib import Path


def load_mind_monitor_csv(csv_path, quality_filter=True):
    """
    Mind Monitor CSVファイルを読み込む

    Parameters
    ----------
    csv_path : str or Path
        CSVファイルのパス
    quality_filter : bool
        True の場合、HeadBandOn=1 のデータのみ抽出

    Returns
    -------
    df : pd.DataFrame
        読み込んだデータフレーム（Time_sec列を追加）
    """
    df = pd.read_csv(csv_path, low_memory=False)

    # タイムスタンプをDatetime型に変換
    df['TimeStamp'] = pd.to_datetime(df['TimeStamp'])

    # 相対時間 (秒) を計算
    df['Time_sec'] = (df['TimeStamp'] - df['TimeStamp'].iloc[0]).dt.total_seconds()

    # 品質フィルタリング
    if quality_filter:
        df = df[df['HeadBandOn'] == 1].copy()

    return df


def get_optics_data(df):
    """
    OpticsデータをNumPy配列で取得

    Parameters
    ----------
    df : pd.DataFrame
        Mind Monitorデータフレーム

    Returns
    -------
    optics_dict : dict
        {
            'left_730': np.ndarray,
            'left_850': np.ndarray,
            'right_730': np.ndarray,
            'right_850': np.ndarray,
            'time': np.ndarray
        }
    """
    return {
        'left_730': df['Optics1'].values,   # 730nm Left Inner
        'left_850': df['Optics3'].values,   # 850nm Left Inner
        'right_730': df['Optics2'].values,  # 730nm Right Inner
        'right_850': df['Optics4'].values,  # 850nm Right Inner
        'time': df['Time_sec'].values
    }


def get_heart_rate_data(df):
    """
    心拍数データを取得（0を除外）

    Parameters
    ----------
    df : pd.DataFrame
        Mind Monitorデータフレーム

    Returns
    -------
    hr_dict : dict
        {
            'heart_rate': np.ndarray,
            'time': np.ndarray
        }
    """
    df_hr = df[df['Heart_Rate'] > 0].copy()

    return {
        'heart_rate': df_hr['Heart_Rate'].values,
        'time': df_hr['Time_sec'].values,
        'timestamps': df_hr['TimeStamp'].values
    }


def get_data_summary(df):
    """
    データの概要統計を取得

    Parameters
    ----------
    df : pd.DataFrame
        Mind Monitorデータフレーム

    Returns
    -------
    summary : dict
        統計情報の辞書
    """
    duration = df['Time_sec'].max()

    return {
        'total_records': len(df),
        'duration_sec': duration,
        'duration_min': duration / 60,
        'sampling_rate_hz': len(df) / duration if duration > 0 else 0,
        'optics_channels': sum(1 for i in range(1, 17) if f'Optics{i}' in df.columns and df[f'Optics{i}'].sum() > 0),
        'valid_heart_rate_records': (df['Heart_Rate'] > 0).sum(),
    }
