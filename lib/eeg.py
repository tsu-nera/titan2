"""
高レベルEEG解析ユーティリティ

時間セグメント分析など、レポート生成で利用する追加機能を提供する。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, TYPE_CHECKING

import numpy as np
import pandas as pd
from scipy import stats

from .sensors.eeg.frontal_theta import (
    FrontalThetaResult,
    calculate_frontal_theta,
)
from .sensors.eeg.preprocessing import filter_eeg_quality

if TYPE_CHECKING:
    import mne


# ========================================
# 総合スコア算出の重み定数
# ========================================
MEDITATION_SCORE_WEIGHTS = {
    'fmtheta': 0.3125,          # Frontal Midline Theta（瞑想深度）
    'spectral_entropy': 0.25,   # Spectral Entropy（集中度）
    'theta_alpha_ratio': 0.1875, # θ/α比（瞑想深度）
    'alpha_beta_ratio': 0.125,  # α/β比（リラックス度）
    'iaf_stability': 0.125,     # IAF安定性（周波数特性）
}


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
    iaf_series: Optional[pd.Series] = None,
    warmup_minutes: float = 0.0,
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
    iaf_series : pd.Series, optional
        IAF（Individual Alpha Frequency）の時系列データ（indexはタイムスタンプ）。
    warmup_minutes : float, default 0.0
        セッション開始後の除外期間（分単位）。アーティファクト除去のため。

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

    # ウォームアップ期間を除外
    original_start = df_clean['TimeStamp'].iloc[0]
    session_start = original_start + pd.Timedelta(minutes=warmup_minutes)
    session_end = df_clean['TimeStamp'].iloc[-1]

    # ウォームアップ後のデータのみを使用
    df_clean = df_clean[df_clean['TimeStamp'] >= session_start]
    if df_clean.empty:
        raise ValueError(f'ウォームアップ期間（{warmup_minutes}分）除外後、有効なデータがありません。')

    freq_str = f'{int(segment_minutes)}T'
    segment_delta = pd.Timedelta(minutes=segment_minutes)

    # Fmθ時系列（ウォームアップ期間を除外）
    fmtheta_series = fmtheta_series.sort_index()
    fmtheta_series = fmtheta_series[fmtheta_series.index >= session_start]

    # IAF時系列（渡されている場合、ウォームアップ期間を除外）
    if iaf_series is not None:
        iaf_series = iaf_series.sort_index()
        iaf_series = iaf_series[iaf_series.index >= session_start]

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

        # Fmθ平均の計算（外れ値除去）
        fm_clean = fm_slice.dropna()
        if len(fm_clean) > 3:  # 最低限のサンプル数が必要
            z_scores = np.abs(stats.zscore(fm_clean))
            fm_filtered = fm_clean[z_scores < 3.0]
            fm_mean = fm_filtered.mean() if len(fm_filtered) > 0 else fm_clean.mean()
        else:
            fm_mean = fm_clean.mean() if len(fm_clean) > 0 else np.nan

        # IAF平均（渡されている場合）
        iaf_mean = np.nan
        if iaf_series is not None:
            iaf_slice = iaf_series.loc[(iaf_series.index >= start) & (iaf_series.index < end)]
            iaf_mean = iaf_slice.mean()

        def _segment_mean(series: pd.Series) -> float:
            if series.empty:
                return np.nan
            window = series.loc[(series.index >= start) & (series.index < end)]
            return window.mean()

        alpha_mean = _segment_mean(band_series['Alpha'])
        beta_mean = _segment_mean(band_series['Beta'])
        theta_mean = _segment_mean(band_series['Theta'])

        # θ/α比: 対数値（Bels）なので引き算でlog(theta/alpha)を計算
        theta_alpha_ratio = np.nan
        if pd.notna(alpha_mean) and pd.notna(theta_mean):
            theta_alpha_ratio = theta_mean - alpha_mean

        # α/β比: 対数値（Bels）なので引き算でlog(alpha/beta)を計算
        alpha_beta_ratio_log = np.nan
        if pd.notna(alpha_mean) and pd.notna(beta_mean):
            alpha_beta_ratio_log = alpha_mean - beta_mean
            # 実数値に戻す（Belsから線形スケールへ）
            alpha_beta_ratio = 10 ** alpha_beta_ratio_log
        else:
            alpha_beta_ratio = np.nan

        # IAF変動係数
        iaf_cv = np.nan
        if iaf_series is not None and len(iaf_slice) > 1:
            iaf_std = iaf_slice.std()
            iaf_val = iaf_slice.mean()
            if pd.notna(iaf_val) and iaf_val != 0:
                iaf_cv = iaf_std / iaf_val

        # 総合スコア計算（利用可能な指標のみ）
        segment_score_result = calculate_meditation_score(
            fmtheta=fm_mean,
            spectral_entropy=None,  # セグメント単位では未対応
            theta_alpha_ratio=theta_alpha_ratio,
            faa=None,  # セグメント単位では未対応
            alpha_beta_ratio=alpha_beta_ratio,
            iaf_cv=iaf_cv,
            hsi_quality=None,  # セグメント単位では未対応（全体品質を使用するオプション）
        )
        meditation_score = segment_score_result['total_score']

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
            'iaf_mean': iaf_mean,
            'alpha_mean': alpha_mean,
            'beta_mean': beta_mean,
            'theta_mean': theta_mean,
            'theta_alpha_ratio': theta_alpha_ratio,
            'meditation_score': meditation_score,
        })

    segment_frame = pd.DataFrame(records)
    segment_frame['label'] = [
        f"{row['segment_start'].strftime('%H:%M')} - {row['segment_end'].strftime('%H:%M')}"
        for _, row in segment_frame.iterrows()
    ]

    if segment_frame.empty:
        raise ValueError('時間セグメント分析の結果が空です。')

    # 正規化スコア
    numeric_cols = ['fmtheta_mean', 'iaf_mean', 'alpha_mean', 'beta_mean', 'theta_alpha_ratio']
    metrics_df = segment_frame.set_index('segment_index')[numeric_cols]
    normalized = pd.DataFrame(
        {col: _min_max_normalize(metrics_df[col]) for col in metrics_df.columns}
    )
    normalized = normalized.reindex(metrics_df.index)

    # ピーク判定（総合スコアベース）
    meditation_scores = segment_frame.set_index('segment_index')['meditation_score']
    if meditation_scores.dropna().empty:
        peak_idx = None
        peak_score = pd.Series(dtype=float)
    else:
        peak_score = meditation_scores
        peak_idx = int(peak_score.idxmax())

    # 表形式（日本語ラベル）
    display_rows = []
    for (idx, row), comment in zip(segment_frame.iterrows(), comments):
        display_rows.append({
            'セグメント': f"セグメント{int(row['segment_index'])}",
            '時間帯': row['label'],
            'Fmθ平均 (μV²)': row['fmtheta_mean'],
            'IAF平均 (Hz)': row['iaf_mean'],
            'Alpha平均 (Bels)': row['alpha_mean'],
            'Beta平均 (Bels)': row['beta_mean'],
            'θ/α比 (Bels)': row['theta_alpha_ratio'],
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


def _normalize_indicator(
    value: float,
    min_val: float,
    max_val: float,
    reverse: bool = False,
) -> float:
    """
    指標を0-1に正規化する。

    Parameters
    ----------
    value : float
        正規化する値
    min_val : float
        最小値（この値が0になる）
    max_val : float
        最大値（この値が1になる）
    reverse : bool
        Trueの場合、値が低いほど良い指標として逆転（例：SE、HSI品質）

    Returns
    -------
    float
        正規化された値（0-1）
    """
    if pd.isna(value):
        return 0.5  # 欠損値はデフォルト0.5

    # クリッピング
    clipped = np.clip(value, min_val, max_val)

    # 正規化
    if np.isclose(max_val, min_val):
        normalized = 0.5
    else:
        normalized = (clipped - min_val) / (max_val - min_val)

    # 逆転（低いほど良い指標）
    if reverse:
        normalized = 1.0 - normalized

    return normalized


def calculate_meditation_score(
    fmtheta: Optional[float] = None,
    spectral_entropy: Optional[float] = None,
    theta_alpha_ratio: Optional[float] = None,
    faa: Optional[float] = None,
    alpha_beta_ratio: Optional[float] = None,
    iaf_cv: Optional[float] = None,
    hsi_quality: Optional[float] = None,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, object]:
    """
    瞑想セッションの総合スコアを計算する。

    Parameters
    ----------
    fmtheta : float, optional
        Frontal Midline Thetaパワー（μV²）
    spectral_entropy : float, optional
        Spectral Entropy（0-1正規化済み）
    theta_alpha_ratio : float, optional
        θ/α比（Bels差）
    faa : float, optional
        Frontal Alpha Asymmetry（ln(μV²)）
    alpha_beta_ratio : float, optional
        α/β比（無次元）
    iaf_cv : float, optional
        IAF変動係数（0-1、低いほど安定）
    hsi_quality : float, optional
        HSI品質スコア（1.0=Good, 4.0=Bad）
    weights : dict, optional
        重み辞書（指定しない場合はMEDITATION_SCORE_WEIGHTSを使用）

    Returns
    -------
    dict
        {
            'total_score': 総合スコア（0-100点）,
            'level': 評価レベル（優秀/良好/普通/要改善）,
            'scores': {指標名: 個別スコア（0-1）},
            'weights': 使用した重み辞書
        }
    """
    if weights is None:
        weights = MEDITATION_SCORE_WEIGHTS

    scores = {}

    # Fmθスコア（高いほど良い）
    if fmtheta is not None:
        scores['fmtheta'] = _normalize_indicator(fmtheta, min_val=50.0, max_val=200.0)
    else:
        scores['fmtheta'] = 0.5

    # SEスコア（低いほど良い、逆転）
    # 注: SEは通常0.7-1.0の範囲に収まるため、この範囲で正規化
    if spectral_entropy is not None:
        scores['spectral_entropy'] = _normalize_indicator(
            spectral_entropy, min_val=0.7, max_val=1.0, reverse=True
        )
    else:
        scores['spectral_entropy'] = 0.5

    # θ/α比スコア（高いほど良い）
    if theta_alpha_ratio is not None:
        scores['theta_alpha_ratio'] = _normalize_indicator(
            theta_alpha_ratio, min_val=-1.0, max_val=1.0
        )
    else:
        scores['theta_alpha_ratio'] = 0.5

    # FAAスコア（正値ほど良い、中心化）
    if faa is not None:
        scores['faa'] = _normalize_indicator(faa, min_val=-0.5, max_val=0.5)
    else:
        scores['faa'] = 0.5

    # α/β比スコア（高いほど良い）
    if alpha_beta_ratio is not None:
        scores['alpha_beta_ratio'] = _normalize_indicator(
            alpha_beta_ratio, min_val=1.0, max_val=10.0
        )
    else:
        scores['alpha_beta_ratio'] = 0.5

    # IAF安定性スコア（変動係数が低いほど良い、逆転）
    if iaf_cv is not None:
        scores['iaf_stability'] = _normalize_indicator(
            iaf_cv, min_val=0.0, max_val=0.05, reverse=True
        )
    else:
        scores['iaf_stability'] = 0.5

    # 品質スコア（1.0=Good、4.0=Bad、逆変換）
    if hsi_quality is not None:
        scores['quality'] = _normalize_indicator(
            hsi_quality, min_val=1.0, max_val=4.0, reverse=True
        )
    else:
        scores['quality'] = 0.5

    # 重み付け平均で総合スコア算出（weightsに存在するキーのみ使用）
    total_score = sum(scores[key] * weights[key] for key in weights.keys() if key in scores)
    total_score_100 = total_score * 100.0

    # 評価レベル判定
    if total_score_100 >= 80:
        level = "優秀"
    elif total_score_100 >= 65:
        level = "良好"
    elif total_score_100 >= 50:
        level = "普通"
    else:
        level = "要改善"

    return {
        'total_score': total_score_100,
        'level': level,
        'scores': scores,
        'weights': weights,
    }
