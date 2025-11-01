#!/usr/bin/env python3
"""
Muse脳波データ基本分析スクリプト

lib/eeg.py の関数を使用してマークダウンレポートを生成します。

Usage:
    python generate_report.py --data <CSV_PATH> [--output <REPORT_PATH>]
"""

import sys
from pathlib import Path
import argparse
from datetime import datetime

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# プロジェクトルートをパスに追加
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# lib モジュールから関数をインポート
from lib import (
    load_mind_monitor_csv,
    calculate_band_statistics,
    calculate_hsi_statistics,
    prepare_mne_raw,
    filter_eeg_quality,
    calculate_psd,
    calculate_spectrogram,
    calculate_band_ratios,
    calculate_paf,
    calculate_paf_time_evolution,
    plot_band_power_time_series,
    plot_psd,
    plot_psd_time_series,
    plot_spectrogram,
    plot_band_ratios,
    plot_paf,
    plot_paf_time_evolution,
    get_psd_peak_frequencies,
    setup_japanese_font,
    calculate_frontal_theta,
    plot_frontal_theta,
    calculate_segment_analysis,
    plot_segment_comparison,
    get_optics_data,
    analyze_fnirs,
    plot_fnirs_muse_style,
)


def format_timestamp_for_report(value):
    """Datetime表示を秒精度に整形"""
    if value is None:
        return 'N/A'
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    if hasattr(value, 'strftime'):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return str(value)


def seconds_to_minutes(value):
    """秒を分表示用に変換"""
    try:
        return float(value) / 60.0
    except (TypeError, ValueError):
        return None


def generate_fnirs_stats_table(fnirs_stats: dict) -> pd.DataFrame:
    """fNIRS統計情報をDataFrame化して整形"""
    df_stats = pd.DataFrame(fnirs_stats).T
    df_stats = df_stats.rename(
        index={"left": "左半球", "right": "右半球"},
        columns={
            "hbo_mean": "HbO平均",
            "hbo_std": "HbO標準偏差",
            "hbo_min": "HbO最小",
            "hbo_max": "HbO最大",
            "hbr_mean": "HbR平均",
            "hbr_std": "HbR標準偏差",
            "hbr_min": "HbR最小",
            "hbr_max": "HbR最大",
        },
    )
    return df_stats[
        [
            "HbO平均",
            "HbO標準偏差",
            "HbO最小",
            "HbO最大",
            "HbR平均",
            "HbR標準偏差",
            "HbR最小",
            "HbR最大",
        ]
    ]


def generate_markdown_report(data_path, output_dir, results):
    """
    マークダウンレポートを生成

    Parameters
    ----------
    data_path : Path
        入力CSVファイルパス
    output_dir : Path
        出力ディレクトリ
    results : dict
        分析結果を格納した辞書
    """
    report_path = output_dir / 'REPORT.md'

    print(f'生成中: マークダウンレポート -> {report_path}')

    info = results.get('data_info', {})

    start_time = format_timestamp_for_report(info.get('start_time'))
    end_time = format_timestamp_for_report(info.get('end_time'))
    duration_min = seconds_to_minutes(info.get('duration_sec'))
    duration_str = f"{duration_min:.1f} 分" if duration_min is not None else "N/A"

    report = f"""# Muse脳波データ分析レポート

- **生成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **データファイル**: `{data_path.name}`
- **記録時間**: {start_time} ~ {end_time}
- **計測時間**: {duration_str}

---

"""

    # ========================================
    # 接続品質（HSI）
    # ========================================
    if 'hsi_stats' in results:
        hsi_data = results['hsi_stats']
        overall_quality = hsi_data.get('overall_quality')
        good_ratio = hsi_data.get('good_ratio', 0.0) * 100

        report += "## 📡 接続品質\n\n"

        # 全体評価
        if overall_quality is not None:
            if overall_quality <= 1.5:
                quality_label = '優秀'
            elif overall_quality <= 2.5:
                quality_label = '良好'
            else:
                quality_label = '要改善'

            report += f"- **総合品質**: {quality_label} (スコア: {overall_quality:.2f})\n"
            report += f"- **Good品質率**: {good_ratio:.1f}%\n\n"

        # チャネル別詳細
        if not hsi_data['statistics'].empty:
            report += "### チャネル別詳細\n\n"
            report += hsi_data['statistics'].to_markdown(index=False, floatfmt='.2f')
            report += "\n\n"
            report += "> **注**: 1.0=Good, 2.0=Medium, 4.0=Bad\n\n"

    # ========================================
    # 分析サマリー
    # ========================================
    report += "## 📊 分析サマリー\n\n"

    # セッション総合評価
    if 'band_ratios_stats' in results:
        report += "### セッション総合評価\n\n"
        for _, row in results['band_ratios_stats'].iterrows():
            ratio_name = row['指標']
            avg_value = row['平均値']

            if 'リラックス' in ratio_name:
                level = 'とても高い' if avg_value > 2.0 else '高い' if avg_value > 1.0 else '普通'
            elif '集中' in ratio_name:
                level = 'とても高い' if avg_value > 2.0 else '高い' if avg_value > 1.0 else '普通'
            elif '瞑想' in ratio_name:
                level = '深い' if avg_value > 1.5 else '中程度' if avg_value > 0.8 else '浅い'
            else:
                level = '不明'

            report += f"- **{ratio_name}**: {avg_value:.3f} ({level})\n"
        report += "\n"

    # ピークパフォーマンス区間
    segment_keys = {'segment_table', 'segment_plot', 'segment_peak_range'}
    if any(key in results for key in segment_keys):
        peak_range = results.get('segment_peak_range')
        peak_score = results.get('segment_peak_score')
        if peak_range:
            report += "### ピークパフォーマンス\n\n"
            if peak_score is not None:
                report += f"- **最高パフォーマンス区間**: {peak_range} (スコア: {peak_score:.2f})\n\n"
            else:
                report += f"- **最高パフォーマンス区間**: {peak_range}\n\n"

    # ========================================
    # 周波数帯域分析
    # ========================================
    band_power_keys = {
        'band_power_img',
        'psd_img',
        'spectrogram_img'
    }
    if any(key in results for key in band_power_keys):
        report += "## 🧠 周波数帯域分析\n\n"

        if 'band_power_img' in results:
            report += "### バンドパワー時系列\n\n"
            report += f"![バンドパワー時系列](img/{results['band_power_img']})\n\n"

        if 'psd_img' in results:
            report += "### パワースペクトル密度（PSD）\n\n"
            report += f"![PSD](img/{results['psd_img']})\n\n"

        if 'spectrogram_img' in results:
            report += "### スペクトログラム\n\n"
            report += f"![スペクトログラム](img/{results['spectrogram_img']})\n\n"

    # ========================================
    # 特徴的指標分析
    # ========================================
    fmtheta_keys = {'frontal_theta_img', 'frontal_theta_stats', 'frontal_theta_increase'}
    paf_keys = {'paf_img', 'paf_summary', 'iaf', 'paf_time_img', 'paf_time_stats'}
    band_ratio_keys = {'band_ratios_img', 'band_ratios_stats'}

    if any(key in results for key in (fmtheta_keys | paf_keys | band_ratio_keys)):
        report += "## 🎯 特徴的指標分析\n\n"

        # Frontal Midline Theta
        if any(key in results for key in fmtheta_keys):
            report += "### Frontal Midline Theta (Fmθ)\n\n"

            if 'frontal_theta_img' in results:
                report += f"![Frontal Midline Theta](img/{results['frontal_theta_img']})\n\n"

            if 'frontal_theta_stats' in results:
                report += results['frontal_theta_stats'].to_markdown(index=False, floatfmt='.3f')
                report += "\n\n"

            if 'frontal_theta_increase' in results:
                inc = results['frontal_theta_increase']
                if pd.notna(inc):
                    report += f"セッション後半の平均Fmθは前半比で **{inc:+.1f}%** 変化しました。\n\n"

        # Peak Alpha Frequency
        if any(key in results for key in paf_keys):
            report += "### Peak Alpha Frequency (PAF)\n\n"

            if 'paf_img' in results:
                report += f"![PAF](img/{results['paf_img']})\n\n"

            if 'iaf' in results:
                iaf_data = results['iaf']
                report += f"**Individual Alpha Frequency (IAF)**: {iaf_data['value']:.2f} ± {iaf_data['std']:.2f} Hz\n\n"

            if 'paf_summary' in results:
                report += "**チャネル別詳細**\n\n"
                report += results['paf_summary'].to_markdown(index=False, floatfmt='.2f')
                report += "\n\n"

        # バンド比率
        if any(key in results for key in band_ratio_keys):
            report += "### バンド比率指標\n\n"

            if 'band_ratios_img' in results:
                report += f"![バンド比率](img/{results['band_ratios_img']})\n\n"

            if 'band_ratios_stats' in results:
                report += results['band_ratios_stats'].to_markdown(index=False, floatfmt='.3f')
                report += "\n\n"

    # ========================================
    # 血流動態分析 (fNIRS)
    # ========================================
    if "fnirs_stats" in results or "fnirs_img" in results:
        report += "## 🩸 血流動態分析 (fNIRS)\n\n"

        if "fnirs_img" in results:
            report += "### HbO/HbR時系列\n\n"
            report += f"![fNIRS時系列](img/{results['fnirs_img']})\n\n"

        if "fnirs_stats" in results:
            report += "### 統計サマリー\n\n"
            report += results["fnirs_stats"].to_markdown(floatfmt=".2f")
            report += "\n\n"

    # ========================================
    # 時間経過分析
    # ========================================
    if any(key in results for key in segment_keys):
        report += "## ⏱️ 時間経過分析\n\n"

        if 'segment_plot' in results:
            report += "### セグメント別パフォーマンス\n\n"
            report += f"![時間セグメント比較](img/{results['segment_plot']})\n\n"

        if 'segment_table' in results:
            report += "### 詳細データ\n\n"
            report += results['segment_table'].to_markdown(index=False, floatfmt='.3f')
            report += "\n\n"

    # ファイルに書き込み
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f'✓ レポート生成完了: {report_path}')


def run_full_analysis(data_path, output_dir):
    """
    完全な分析を実行

    Parameters
    ----------
    data_path : Path
        入力CSVファイルパス
    output_dir : Path
        出力ディレクトリ
    """
    print('='*60)
    print('Muse脳波データ基本分析')
    print('='*60)
    print()

    # 日本語フォント設定
    setup_japanese_font()

    # 画像出力ディレクトリ
    img_dir = output_dir / 'img'
    img_dir.mkdir(exist_ok=True)

    # 分析結果を格納
    results = {}

    # データ読み込み
    print(f'Loading: {data_path}')
    df = load_mind_monitor_csv(data_path, filter_headband=False)

    # データ情報を記録
    results['data_info'] = {
        'shape': df.shape,
        'start_time': df['TimeStamp'].min(),
        'end_time': df['TimeStamp'].max(),
        'duration_sec': (df['TimeStamp'].max() - df['TimeStamp'].min()).total_seconds()
    }

    print(f'データ形状: {df.shape[0]} 行 × {df.shape[1]} 列')
    print(
        f'記録時間: '
        f'{format_timestamp_for_report(results["data_info"]["start_time"])} '
        f'~ {format_timestamp_for_report(results["data_info"]["end_time"])}'
    )
    duration_min = seconds_to_minutes(results["data_info"]["duration_sec"])
    if duration_min is not None:
        print(f'計測時間: {duration_min:.1f} 分\n')
    else:
        print('計測時間: N/A\n')

    # HSI接続品質統計
    print('計算中: 接続品質 (HSI)...')
    hsi_stats = calculate_hsi_statistics(df)
    results['hsi_stats'] = hsi_stats

    # バンド統計
    print('計算中: バンド統計量...')
    band_stats = calculate_band_statistics(df)
    results['band_statistics'] = band_stats['statistics']

    # fNIRS解析
    try:
        optics_data = get_optics_data(df)
        if optics_data and len(optics_data['time']) > 0:
            print('計算中: fNIRS統計...')
            fnirs_results = analyze_fnirs(optics_data)
            results['fnirs_stats'] = generate_fnirs_stats_table(fnirs_results['stats'])

            print('プロット中: fNIRS時系列...')
            fig_fnirs, _ = plot_fnirs_muse_style(fnirs_results)
            fnirs_img_name = 'fnirs_muse_style.png'
            fig_fnirs.savefig(img_dir / fnirs_img_name, dpi=150, bbox_inches='tight')
            plt.close(fig_fnirs)
            results['fnirs_img'] = fnirs_img_name
    except KeyError as exc:
        print(f'警告: fNIRSデータを処理できませんでした ({exc})')

    # バンドパワー時系列（Museアプリ風）
    print('プロット中: バンドパワー時系列...')
    df_quality, quality_mask = filter_eeg_quality(df)
    df_for_band = df_quality if not df_quality.empty else df
    plot_band_power_time_series(
        df_for_band,
        img_path=img_dir / 'band_power_time_series.png',
        rolling_window=200,
        resample_interval='2S',
        smooth_window=9,
        clip_percentile=98.0
    )
    results['band_power_img'] = 'band_power_time_series.png'
    results['band_power_quality_ratio'] = float(quality_mask.mean())

    # MNE RAW準備
    print('準備中: MNE RAWデータ...')
    mne_dict = prepare_mne_raw(df)
    raw = None

    if mne_dict:
        raw = mne_dict['raw']
        print(f'検出されたチャネル: {mne_dict["channels"]}')
        print(f'推定サンプリングレート: {mne_dict["sfreq"]:.2f} Hz')

        # PSD時系列
        print('プロット中: PSDの時間推移...')
        psd_time_img_name = 'psd_time_series.png'
        plot_psd_time_series(
            raw,
            channels=mne_dict['channels'],
            img_path=img_dir / psd_time_img_name,
            fmin=1.0,
            fmax=40.0,
            window_sec=8.0,
            step_sec=2.0,
            clip_percentile=90.0,
            smooth_window=7
        )
        results['psd_time_series_img'] = psd_time_img_name

        # PSD計算
        print('計算中: パワースペクトル密度...')
        psd_dict = calculate_psd(raw)

        # PSDプロット
        print('プロット中: パワースペクトル密度...')
        plot_psd(psd_dict, img_path=img_dir / 'psd.png')
        results['psd_img'] = 'psd.png'

        # ピーク周波数
        results['psd_peaks'] = get_psd_peak_frequencies(psd_dict)

        # スペクトログラム
        print('計算中: スペクトログラム...')
        tfr_dict = calculate_spectrogram(raw, channel='RAW_TP9')

        if tfr_dict:
            print('プロット中: スペクトログラム...')
            plot_spectrogram(tfr_dict, img_path=img_dir / 'spectrogram.png')
            results['spectrogram_img'] = 'spectrogram.png'

        # PAF分析
        print('計算中: Peak Alpha Frequency...')
        paf_dict = calculate_paf(psd_dict)

        # PAFプロット
        print('プロット中: PAF...')
        plot_paf(paf_dict, img_path=img_dir / 'paf.png')
        results['paf_img'] = 'paf.png'

        # PAFサマリー
        paf_summary = []
        for ch_label, paf_result in paf_dict['paf_by_channel'].items():
            paf_summary.append({
                'チャネル': ch_label,
                'PAF (Hz)': paf_result['PAF'],
                'Power (μV²/Hz)': paf_result['Power']
            })
        results['paf_summary'] = pd.DataFrame(paf_summary)
        results['iaf'] = {'value': paf_dict['iaf'], 'std': paf_dict['iaf_std']}

        # PAF時間推移
        if tfr_dict:
            print('計算中: PAF時間推移...')
            paf_time_dict = calculate_paf_time_evolution(tfr_dict, paf_dict)

            print('プロット中: PAF時間推移...')
            plot_paf_time_evolution(paf_time_dict, df, paf_dict, img_path=img_dir / 'paf_time_evolution.png')
            results['paf_time_img'] = 'paf_time_evolution.png'
            results['paf_time_stats'] = paf_time_dict['stats']

    # Frontal Midline Theta解析
    fmtheta_result = None
    try:
        print('計算中: Frontal Midline Theta...')
        fmtheta_result = calculate_frontal_theta(df, raw=raw if mne_dict else None)
        print('プロット中: Frontal Midline Theta...')
        plot_frontal_theta(
            fmtheta_result,
            img_path=img_dir / 'frontal_midline_theta.png'
        )
        results['frontal_theta_img'] = 'frontal_midline_theta.png'
        results['frontal_theta_stats'] = fmtheta_result.statistics
        results['frontal_theta_increase'] = fmtheta_result.metadata.get('increase_rate_percent')
    except Exception as exc:
        print(f'警告: Fmθ解析に失敗しました ({exc})')

    # 時間セグメント分析
    try:
        print('計算中: 時間セグメント分析...')

        # IAF時系列の準備（PAF時間推移から）
        iaf_series = None
        if 'paf_time_img' in results and paf_time_dict:
            # PAF時間推移のタイムスタンプとIAF値をSeriesに変換
            session_start = df['TimeStamp'].iloc[0]
            iaf_times = pd.to_datetime(session_start) + pd.to_timedelta(paf_time_dict['times'], unit='s')
            iaf_series = pd.Series(paf_time_dict['paf_smoothed'], index=iaf_times)

        segment_result = calculate_segment_analysis(
            df_quality,
            fmtheta_result.time_series,
            segment_minutes=5,
            iaf_series=iaf_series,
        )
        print('プロット中: 時間セグメント比較...')
        segment_plot_name = 'time_segment_metrics.png'
        plot_segment_comparison(
            segment_result,
            img_path=img_dir / segment_plot_name,
        )
        results['segment_table'] = segment_result.table
        results['segment_plot'] = segment_plot_name
        results['segment_peak_range'] = segment_result.metadata.get('peak_time_range')
        results['segment_peak_score'] = segment_result.metadata.get('peak_score')
    except Exception as exc:
        print(f'警告: 時間セグメント分析に失敗しました ({exc})')

    # バンド比率
    print('計算中: バンド比率...')
    ratios_dict = calculate_band_ratios(df)

    print('プロット中: バンド比率...')
    plot_band_ratios(
        ratios_dict,
        img_path=img_dir / 'band_ratios.png',
        clip_percentile=95.0,
        smooth_window=5
    )
    results['band_ratios_img'] = 'band_ratios.png'
    results['band_ratios_stats'] = ratios_dict['statistics']
    results['spike_analysis'] = ratios_dict['spike_analysis']

    # レポート生成
    generate_markdown_report(data_path, output_dir, results)

    print()
    print('='*60)
    print('分析完了!')
    print('='*60)
    print(f'レポート: {output_dir / "REPORT.md"}')
    print(f'画像: {img_dir}/')


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='Muse脳波データの基本分析とレポート生成（リファクタリング版）'
    )
    parser.add_argument(
        '--data',
        type=Path,
        required=True,
        help='入力CSVファイルパス'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path(__file__).parent,
        help='出力ディレクトリ（デフォルト: スクリプトと同じディレクトリ）'
    )

    args = parser.parse_args()

    # パスの検証
    if not args.data.exists():
        print(f'エラー: データファイルが見つかりません: {args.data}')
        return 1

    args.output.mkdir(parents=True, exist_ok=True)

    # 分析実行
    run_full_analysis(args.data, args.output)

    return 0


if __name__ == '__main__':
    exit(main())
