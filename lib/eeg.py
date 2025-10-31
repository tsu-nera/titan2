"""
高レベルEEG解析ユーティリティ

時間セグメント分析など、レポート生成で利用する追加機能を提供する。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, TYPE_CHECKING

import numpy as np
import pandas as pd

from .sensors.eeg.frontal_theta import (
    FrontalThetaResult,
    calculate_frontal_theta,
)
from .sensors.eeg.preprocessing import filter_signal_quality

if TYPE_CHECKING:
    import mne


@dataclass
class SegmentAnalysisResult:
    """時間セグメント分析の結果を保持する。"""

    segments: pd.DataFrame
    table: pd.DataFrame
    normalized: pd.DataFrame
    metadata: Dict[str, object]

    def to_markdown(self, floatfmt: str = '.3f') -> str:
        """集計表をMarkdown文字列として返す。"""
        return self.table.to_markdown(index=False, floatfmt=floatfmt)


def _min_max_normalize(series: pd.Series) -> pd.Series:
    """0-1レンジへ正規化（定数列は0.5で埋める）。"""
    clean = series.dropna()
    if clean.empty:
        return pd.Series(np.nan, index=series.index)

    min_val = clean.min()
    max_val = clean.max()

    if pd.isna(min_val) or pd.isna(max_val) or np.isclose(max_val, min_val):
        return pd.Series(0.5, index=series.index)

    return (series - min_val) / (max_val - min_val)


def calculate_segment_analysis(
    df_clean: pd.DataFrame,
    fmtheta_series: pd.Series,
    segment_minutes: int = 5,
    band_means: Optional[Dict[str, pd.Series]] = None,
) -> SegmentAnalysisResult:
    """
    セッションを一定時間のセグメントに分割し、主要指標を算出する。

    Parameters
    ----------
    df_clean : pd.DataFrame
        前処理済みMind Monitor形式のデータフレーム。
    fmtheta_series : pd.Series
        Fmθの時系列データ（indexはタイムスタンプ）。
    segment_minutes : int, default 5
        セグメント長（分単位）。
    band_means : dict of pd.Series, optional
        事前計算されたバンド平均値の辞書 {'Alpha': series, 'Beta': series, 'Theta': series}。
        未指定の場合は内部で計算する。

    Returns
    -------
    SegmentAnalysisResult
        集計表・正規化値・メタデータを含む時間セグメント分析結果。
    """
    if 'TimeStamp' not in df_clean.columns:
        raise ValueError('TimeStamp列が存在しません。')
    if segment_minutes <= 0:
        raise ValueError('segment_minutesは正の整数で指定してください。')

    df_clean = df_clean.copy()
    df_clean['TimeStamp'] = pd.to_datetime(df_clean['TimeStamp'], errors='coerce')
    df_clean = df_clean.dropna(subset=['TimeStamp']).sort_values('TimeStamp')
    if df_clean.empty:
        raise ValueError('有効なTimeStampを持つデータがありません。')

    session_start = df_clean['TimeStamp'].iloc[0]
    session_end = df_clean['TimeStamp'].iloc[-1]
    freq_str = f'{int(segment_minutes)}T'
    segment_delta = pd.Timedelta(minutes=segment_minutes)

    # Fmθ時系列
    fmtheta_series = fmtheta_series.sort_index()

    # バンド別の平均値（外部から渡されない場合は内部で計算）
    if band_means is None:
        band_series: Dict[str, pd.Series] = {}
        for band in ('Alpha', 'Beta', 'Theta'):
            cols = [c for c in df_clean.columns if c.startswith(f'{band}_')]
            if not cols:
                band_series[band] = pd.Series(dtype=float)
                continue
            numeric = df_clean[cols].apply(pd.to_numeric, errors='coerce')
            band_mean = numeric.mean(axis=1)
            band_mean.index = df_clean['TimeStamp']
            band_series[band] = band_mean.sort_index()
    else:
        band_series = band_means

    # セグメント境界の生成
    segment_starts = []
    current = session_start
    while current < session_end:
        segment_starts.append(current)
        current += segment_delta
    if not segment_starts:
        segment_starts = [session_start]

    records = []
    comments = []

    for idx, start in enumerate(segment_starts, start=1):
        end = min(start + segment_delta, session_end)
        clean_mask = (df_clean['TimeStamp'] >= start) & (df_clean['TimeStamp'] < end)
        clean_slice_exists = clean_mask.any()

        fm_slice = fmtheta_series.loc[(fmtheta_series.index >= start) & (fmtheta_series.index < end)]
        fm_mean = fm_slice.mean()

        def _segment_mean(series: pd.Series) -> float:
            if series.empty:
                return np.nan
            window = series.loc[(series.index >= start) & (series.index < end)]
            return window.mean()

        alpha_mean = _segment_mean(band_series['Alpha'])
        beta_mean = _segment_mean(band_series['Beta'])
        theta_mean = _segment_mean(band_series['Theta'])

        theta_alpha_ratio = np.nan
        if pd.notna(alpha_mean) and alpha_mean != 0:
            theta_alpha_ratio = theta_mean / alpha_mean

        clean_count = int(clean_mask.sum())

        comment_parts = []
        if not clean_slice_exists:
            comment_parts.append('データ不足')
        if fm_slice.dropna().empty:
            comment_parts.append('Fmθデータ不足')
        comments.append(' / '.join(comment_parts) if comment_parts else '')

        records.append({
            'segment_index': idx,
            'segment_start': start,
            'segment_end': end,
            'fmtheta_mean': fm_mean,
            'alpha_mean': alpha_mean,
            'beta_mean': beta_mean,
            'theta_mean': theta_mean,
            'theta_alpha_ratio': theta_alpha_ratio,
        })

    segment_frame = pd.DataFrame(records)
    segment_frame['label'] = [
        f"{row['segment_start'].strftime('%H:%M')} - {row['segment_end'].strftime('%H:%M')}"
        for _, row in segment_frame.iterrows()
    ]

    if segment_frame.empty:
        raise ValueError('時間セグメント分析の結果が空です。')

    # 正規化スコア
    numeric_cols = ['fmtheta_mean', 'alpha_mean', 'beta_mean', 'theta_alpha_ratio']
    metrics_df = segment_frame.set_index('segment_index')[numeric_cols]
    normalized = pd.DataFrame(
        {col: _min_max_normalize(metrics_df[col]) for col in metrics_df.columns}
    )
    normalized = normalized.reindex(metrics_df.index)

    # ピーク判定（Fmθとθ/α比の平均）
    peak_candidates = normalized[['fmtheta_mean', 'theta_alpha_ratio']]
    peak_candidates = peak_candidates.dropna(how='all')
    if peak_candidates.empty:
        peak_idx = None
        peak_score = pd.Series(dtype=float)
    else:
        peak_score = peak_candidates.mean(axis=1)
        peak_idx = int(peak_score.idxmax())

    # 表形式（日本語ラベル）
    display_rows = []
    for (idx, row), comment in zip(segment_frame.iterrows(), comments):
        display_rows.append({
            'セグメント': f"セグメント{int(row['segment_index'])}",
            '時間帯': row['label'],
            'Fmθ平均 (μV²)': row['fmtheta_mean'],
            'Alpha平均 (μV²)': row['alpha_mean'],
            'Beta平均 (μV²)': row['beta_mean'],
            'θ/α比': row['theta_alpha_ratio'],
            '備考': comment,
            'ピーク': '★' if (peak_idx is not None and int(row['segment_index']) == peak_idx) else '',
        })

    table = pd.DataFrame(display_rows)

    metadata = {
        'segment_minutes': segment_minutes,
        'session_start': session_start,
        'session_end': session_end,
        'peak_segment_index': peak_idx,
        'peak_time_range': (
            segment_frame.set_index('segment_index').loc[peak_idx, 'label']
            if peak_idx is not None
            else None
        ),
        'peak_score': float(peak_score.loc[peak_idx]) if peak_idx is not None else None,
    }

    segments = segment_frame.set_index('segment_index')
    segments['segment_index'] = segments.index

    return SegmentAnalysisResult(
        segments=segments,
        table=table,
        normalized=normalized,
        metadata=metadata,
    )


def plot_segment_comparison(
    result: SegmentAnalysisResult,
    img_path: Optional[str] = None,
    title: Optional[str] = None,
) -> 'matplotlib.figure.Figure':
    """
    セグメントごとの主要指標を可視化する。

    Parameters
    ----------
    result : SegmentAnalysisResult
        `calculate_segment_analysis` の戻り値。
    img_path : str, optional
        保存先パス（Noneなら保存しない）。
    title : str, optional
        グラフタイトル。

    Returns
    -------
    matplotlib.figure.Figure
        生成したFigureオブジェクト。
    """
    import matplotlib.pyplot as plt

    if result.normalized.empty:
        raise ValueError('プロット対象のセグメントデータが空です。')

    metric_labels = {
        'fmtheta_mean': 'Fmθ',
        'alpha_mean': 'Alpha',
        'beta_mean': 'Beta',
        'theta_alpha_ratio': 'θ/α比',
    }
    colors = {
        'fmtheta_mean': '#1f77b4',
        'alpha_mean': '#2ca02c',
        'beta_mean': '#ff7f0e',
        'theta_alpha_ratio': '#9467bd',
    }

    segments = result.segments
    x_positions = np.arange(len(segments))
    xtick_labels = segments['label'].tolist()

    fig, ax = plt.subplots(figsize=(11, 6))

    for metric in result.normalized.columns:
        series = result.normalized[metric]
        if series.isna().all():
            continue
        ax.plot(
            x_positions,
            series.values,
            marker='o',
            linewidth=2.2,
            label=metric_labels.get(metric, metric),
            color=colors.get(metric, None),
        )

    peak_idx = result.metadata.get('peak_segment_index')
    if peak_idx is not None:
        peak_pos = segments.index.get_loc(peak_idx)
        ax.axvspan(
            peak_pos - 0.35,
            peak_pos + 0.35,
            color='gold',
            alpha=0.18,
            label='Peak Segment' if 'Peak Segment' not in ax.get_legend_handles_labels()[1] else None,
        )

    ax.set_xticks(x_positions)
    ax.set_xticklabels(xtick_labels, rotation=30, ha='right')
    ax.set_ylim(0.0, 1.05)
    ax.set_ylabel('正規化スコア (0-1)')
    ax.set_xlabel('時間セグメント')
    ax.set_title(title or '時間セグメント別主要指標', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1.0))
    fig.tight_layout()

    if img_path:
        fig.savefig(img_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

    return fig
