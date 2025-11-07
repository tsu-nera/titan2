#!/usr/bin/env python3
"""
Muse脳波データ基本分析スクリプト（リファクタリング版）

lib/eeg.py の関数を使用してマークダウンレポートを生成します。

Usage:
    python generate_report.py --data <CSV_PATH> [--output <REPORT_PATH>]
"""

import sys
from pathlib import Path
import argparse
from datetime import datetime

import pandas as pd

# プロジェクトルートをパスに追加
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# lib モジュールから関数をインポート
from lib import (
    load_mind_monitor_csv,
    get_data_summary,
    calculate_band_statistics,
    prepare_mne_raw,
    calculate_psd,
    calculate_spectrogram,
    calculate_band_ratios,
    calculate_paf,
    calculate_paf_time_evolution,
    plot_band_power_time_series,
    plot_psd,
    plot_spectrogram,
    plot_band_ratios,
    plot_paf,
    plot_paf_time_evolution,
    get_psd_peak_frequencies,
    FREQ_BANDS
)


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

    report = f"""# Muse脳波データ分析レポート

**生成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**データファイル**: `{data_path.name}`

---

## 1. データ概要

- **データ形状**: {info.get('shape', 'N/A')}
- **記録時間**: {info.get('start_time', 'N/A')} ~ {info.get('end_time', 'N/A')}
- **計測時間**: {info.get('duration_sec', 0):.1f} 秒

"""

    # バンド統計
    if 'band_statistics' in results:
        report += "## 2. 周波数バンド統計\n\n"
        report += results['band_statistics'].to_markdown(index=False, floatfmt='.4f')
        report += "\n\n"
        report += """
**周波数バンドの説明**:
- **Delta (0.5-4 Hz)**: 深い睡眠
- **Theta (4-8 Hz)**: 瞑想、創造性
- **Alpha (8-13 Hz)**: リラックス、目を閉じた状態
- **Beta (13-30 Hz)**: 集中、活動
- **Gamma (30-50 Hz)**: 高度な認知処理

"""

    # バンドパワー時系列
    if 'band_power_img' in results:
        report += "## 3. バンドパワーの時間推移\n\n"
        report += f"![バンドパワー時系列](img/{results['band_power_img']})\n\n"
        report += "Alpha波が高いとリラックス状態、Beta波が高いと集中状態を示します。\n\n"

    # PSD
    if 'psd_img' in results:
        report += "## 4. パワースペクトル密度（PSD）\n\n"
        report += f"![PSD](img/{results['psd_img']})\n\n"

        if 'psd_peaks' in results:
            report += "### 各バンドのピーク周波数\n\n"
            report += results['psd_peaks'].to_markdown(index=False, floatfmt='.2f')
            report += "\n\n"

    # スペクトログラム
    if 'spectrogram_img' in results:
        report += "## 5. スペクトログラム\n\n"
        report += f"![スペクトログラム](img/{results['spectrogram_img']})\n\n"
        report += "時間とともに周波数分布がどう変化するかを可視化しています。\n\n"

    # バンド比率
    if 'band_ratios_img' in results:
        report += "## 6. 脳波指標（バンド比率）\n\n"
        report += f"![バンド比率](img/{results['band_ratios_img']})\n\n"

        if 'band_ratios_stats' in results:
            report += "### 指標サマリー\n\n"
            report += results['band_ratios_stats'].to_markdown(index=False, floatfmt='.3f')
            report += "\n\n"

            # 簡易評価
            report += "### セッション評価\n\n"
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

        if 'spike_analysis' in results:
            report += "### データ品質（スパイク分析）\n\n"
            report += results['spike_analysis'].to_markdown(index=False, floatfmt='.2f')
            report += "\n\n"

    # PAF
    if 'paf_img' in results:
        report += "## 7. Peak Alpha Frequency (PAF) 分析\n\n"
        report += f"![PAF](img/{results['paf_img']})\n\n"

        if 'paf_summary' in results:
            report += "### チャネル別PAF\n\n"
            report += results['paf_summary'].to_markdown(index=False, floatfmt='.2f')
            report += "\n\n"

        if 'iaf' in results:
            iaf_data = results['iaf']
            report += f"**Individual Alpha Frequency (IAF)**: {iaf_data['value']:.2f} ± {iaf_data['std']:.2f} Hz\n\n"

    # PAF時間推移
    if 'paf_time_img' in results:
        report += "### PAFの時間的変化\n\n"
        report += f"![PAF時間推移](img/{results['paf_time_img']})\n\n"

        if 'paf_time_stats' in results:
            stats = results['paf_time_stats']
            report += "#### PAF統計\n\n"
            for key, value in stats.items():
                report += f"- **{key}**: {value:.2f}\n"

            cv = stats['変動係数 (%)']
            if cv < 2:
                stability = '非常に安定'
            elif cv < 5:
                stability = '安定'
            elif cv < 10:
                stability = 'やや変動あり'
            else:
                stability = '変動大'

            report += f"\n**PAF安定性評価**: {stability}\n\n"

    # まとめ
    report += """---

## 8. まとめ

このレポートでは、Museヘッドバンドで取得した脳波データの基本的な分析を行いました。

### 分析内容

1. **データ読み込み**: CSVデータの読み込みと前処理
2. **基本統計**: 各周波数バンドの特性を把握
3. **バンドパワー**: 時間経過に伴う各バンドの変化を追跡
4. **周波数解析**: PSDとスペクトログラムで周波数特性を詳細分析
5. **指標分析**: リラックス度、集中度、瞑想深度の数値化
6. **PAF分析**: Peak Alpha Frequencyの測定と時間変化の追跡

### 次のステップ

詳細な分析については、以下の専門分析を検討してください：

- **左右半球差分析**: 左右半球の非対称性指数（AI）、前頭部Alpha/Beta非対称性
- **サマタ瞑想のfmシータ波分析**: 前頭部シータ波パワー、周波数詳細分析

---

**生成スクリプト**: `generate_report.py`
**分析エンジン**: MNE-Python, pandas, matplotlib
**ライブラリ**: lib/eeg.py
"""

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
    print('Muse脳波データ基本分析（リファクタリング版）')
    print('='*60)
    print()

    # 画像出力ディレクトリ
    img_dir = output_dir / 'img'
    img_dir.mkdir(exist_ok=True)

    # 分析結果を格納
    results = {}

    # データ読み込み
    print(f'Loading: {data_path}')
    df = load_mind_monitor_csv(data_path, quality_filter=False)

    # データ情報を記録
    results['data_info'] = {
        'shape': df.shape,
        'start_time': df['TimeStamp'].min(),
        'end_time': df['TimeStamp'].max(),
        'duration_sec': (df['TimeStamp'].max() - df['TimeStamp'].min()).total_seconds()
    }

    print(f'データ形状: {df.shape[0]} 行 × {df.shape[1]} 列')
    print(f'記録時間: {results["data_info"]["start_time"]} ~ {results["data_info"]["end_time"]}')
    print(f'計測時間: {results["data_info"]["duration_sec"]:.1f} 秒\n')

    # バンド統計
    print('計算中: バンド統計量...')
    band_stats = calculate_band_statistics(df)
    results['band_statistics'] = band_stats['statistics']

    # バンドパワー時系列
    print('プロット中: バンドパワー時系列...')
    plot_band_power_time_series(df, img_path=img_dir / 'band_power_time_series.png')
    results['band_power_img'] = 'band_power_time_series.png'

    # MNE RAW準備
    print('準備中: MNE RAWデータ...')
    mne_dict = prepare_mne_raw(df)

    if mne_dict:
        raw = mne_dict['raw']
        print(f'検出されたチャネル: {mne_dict["channels"]}')
        print(f'推定サンプリングレート: {mne_dict["sfreq"]:.2f} Hz')

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

    # バンド比率
    print('計算中: バンド比率...')
    ratios_dict = calculate_band_ratios(df)

    print('プロット中: バンド比率...')
    plot_band_ratios(ratios_dict, img_path=img_dir / 'band_ratios.png')
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
