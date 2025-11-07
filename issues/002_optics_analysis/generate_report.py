#!/usr/bin/env python3
"""
Muse S fNIRS/PPG Optics Analysis

Mind Monitor CSVから光学センサー（fNIRS/PPG）データを解析し、
マークダウンレポートと可視化画像を生成します。

Usage:
    python generate_report.py --data <CSV_PATH> [--output <OUTPUT_DIR>]
"""

import argparse
from datetime import datetime
from pathlib import Path
import sys

import pandas as pd

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from lib import (  # noqa: E402
    load_mind_monitor_csv,
    get_optics_data,
    get_heart_rate_data,
    get_data_summary,
    analyze_fnirs,
    analyze_respiratory,
    plot_fnirs,
    plot_fnirs_muse_style,
    plot_respiratory,
    plot_frequency_spectrum,
    plot_integrated_dashboard,
)


def parse_args():
    parser = argparse.ArgumentParser(description="fNIRS/PPG光学データ分析レポート生成")
    parser.add_argument(
        "--data",
        required=True,
        help="Mind Monitor CSVファイルへのパス",
    )
    parser.add_argument(
        "--output",
        help="レポートと画像の出力先ディレクトリ（デフォルト: スクリプトディレクトリ）",
    )
    parser.add_argument(
        "--no-font",
        action="store_true",
        help="日本語フォント設定をスキップする場合に指定",
    )
    return parser.parse_args()


def ensure_output_dirs(base_dir: Path) -> Path:
    """
    画像出力ディレクトリを作成してパスを返す。
    """
    base_dir.mkdir(parents=True, exist_ok=True)
    img_dir = base_dir / "img"
    img_dir.mkdir(parents=True, exist_ok=True)
    return img_dir


def generate_fnirs_stats_table(fnirs_stats: dict) -> pd.DataFrame:
    """
    fNIRS統計情報をDataFrame化して整形する。
    """
    df_stats = pd.DataFrame(fnirs_stats).T
    df_stats = df_stats.rename(
        index={
            "left": "左半球",
            "right": "右半球",
        },
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


def generate_respiratory_stats_table(resp_stats: dict) -> pd.DataFrame:
    """
    呼吸推定統計情報をDataFrame化して整形する。
    """
    labels = {
        "rr_mean": "RR平均 (ms)",
        "rr_std": "RR標準偏差 (ms)",
        "rr_min": "RR最小 (ms)",
        "rr_max": "RR最大 (ms)",
        "respiratory_rate_welch": "Welch呼吸数 (breaths/min)",
        "respiratory_rate_fft_mean": "FFT呼吸数平均 (breaths/min)",
        "respiratory_rate_fft_std": "FFT呼吸数標準偏差 (breaths/min)",
    }
    data = {labels[key]: [value] for key, value in resp_stats.items() if key in labels}
    return pd.DataFrame(data)


def format_summary(summary: dict, df: pd.DataFrame) -> dict:
    """
    レポート用のデータ概要情報を整形する。
    """
    start_time = df["TimeStamp"].min() if "TimeStamp" in df.columns else None
    end_time = df["TimeStamp"].max() if "TimeStamp" in df.columns else None

    return {
        "total_records": summary.get("total_records"),
        "duration_sec": summary.get("duration_sec"),
        "duration_min": summary.get("duration_min"),
        "sampling_rate": summary.get("sampling_rate_hz"),
        "optics_channels": summary.get("optics_channels"),
        "valid_heart_rate_records": summary.get("valid_heart_rate_records"),
        "start_time": start_time,
        "end_time": end_time,
    }


def generate_markdown_report(
    data_path: Path,
    output_dir: Path,
    summary_info: dict,
    fnirs_stats_df: pd.DataFrame,
    respiratory_stats_df: pd.DataFrame | None,
    images: dict,
    notes: dict,
) -> Path:
    """
    Markdownレポートを組み立てて保存する。
    """
    report_path = output_dir / "REPORT.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def fmt(value, precision=2):
        if value is None or pd.isna(value):
            return "N/A"
        if isinstance(value, float):
            return f"{value:.{precision}f}"
        return str(value)

    report_lines = [
        "# Muse光学データ統合分析レポート",
        "",
        f"**生成日時**: {timestamp}",
        f"**データファイル**: `{data_path.name}`",
        "",
        "---",
        "",
        "## 1. データ概要",
        "",
        f"- **総レコード数**: {summary_info['total_records']}",
        f"- **計測時間**: {fmt(summary_info['duration_sec'])} 秒 "
        f"({fmt(summary_info['duration_min'])} 分)",
        f"- **推定サンプリングレート**: {fmt(summary_info['sampling_rate'])} Hz",
        f"- **有効Opticsチャネル数**: {summary_info['optics_channels']}",
        f"- **有効心拍レコード数**: {summary_info['valid_heart_rate_records']}",
    ]

    if summary_info["start_time"] and summary_info["end_time"]:
        report_lines.append(
            f"- **記録時間**: {summary_info['start_time']} ~ {summary_info['end_time']}"
        )

    report_lines.extend(
        [
            "",
            "## 2. fNIRS統計サマリー",
            "",
            fnirs_stats_df.to_markdown(floatfmt=".2f"),
            "",
        ]
    )

    if images.get("fnirs_panel"):
        report_lines.extend(
            [
                "### fNIRS時系列（4パネル）",
                "",
                f"![fNIRS 4 Panel]({images['fnirs_panel']})",
                "",
            ]
        )

    if images.get("fnirs_muse_style"):
        report_lines.extend(
            [
                "### fNIRS時系列（Museアプリ風）",
                "",
                f"![fNIRS Muse Style]({images['fnirs_muse_style']})",
                "",
                "HbOの上昇は局所的な血流増加を示し、HbRの低下は酸素消費の高まりを示唆します。",
                "",
            ]
        )

    if respiratory_stats_df is not None:
        report_lines.extend(
            [
                "## 3. 心拍変動と呼吸数推定",
                "",
                respiratory_stats_df.to_markdown(floatfmt=".2f", index=False),
                "",
            ]
        )

        if images.get("resp_timeseries"):
            report_lines.extend(
                [
                    "### 心拍 & 呼吸数の時系列",
                    "",
                    f"![Respiratory Overview]({images['resp_timeseries']})",
                    "",
                ]
            )

        if images.get("resp_psd"):
            report_lines.extend(
                [
                    "### HRVスペクトル（Welch法）",
                    "",
                    f"![Respiratory Spectrum]({images['resp_psd']})",
                    "",
                    "赤色帯が呼吸周波数帯域 (0.15-0.4 Hz) を示します。",
                    "",
                ]
            )
    else:
        report_lines.extend(
            [
                "## 3. 心拍変動と呼吸数推定",
                "",
                "心拍データが不足しているため、呼吸数推定は実行されませんでした。",
                "",
            ]
        )

    if images.get("integrated_dashboard"):
        report_lines.extend(
            [
                "## 4. 統合ダッシュボード",
                "",
                f"![Integrated Dashboard]({images['integrated_dashboard']})",
                "",
                "fNIRSと心拍指標を同一キャンバスで確認できます。変化の同期性を評価する際に活用してください。",
                "",
            ]
        )

    report_lines.extend(
        [
            "## 5. インサイトと所見",
            "",
            "- 左右半球のHbO/HbR振幅を比較し、活動の偏りを評価してください。",
            "- 呼吸数が急峻に変動する区間があれば、fNIRS指標と合わせてストレス反応を検討できます。",
            "- Museアプリ風プロットでは、リアルタイム観察に近い感覚で変化を追跡できます。",
        ]
    )

    if notes:
        report_lines.append("")
        report_lines.append("### 補足メモ")
        report_lines.append("")
        for key, value in notes.items():
            report_lines.append(f"- **{key}**: {value}")

    report_lines.extend(
        [
            "",
            "---",
            "",
            "**生成スクリプト**: `generate_report.py`",
            "**利用ライブラリ**: `lib/sensors/fnirs.py`, `lib/sensors/ppg.py`, `lib/visualization.py`",
        ]
    )

    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"レポートを生成しました: {report_path}")
    return report_path


def main():
    args = parse_args()

    data_path = Path(args.data).expanduser()
    if not data_path.exists():
        raise FileNotFoundError(f"CSVファイルが見つかりません: {data_path}")

    output_dir = (
        Path(args.output).expanduser()
        if args.output
        else Path(__file__).resolve().parent
    )
    img_dir = ensure_output_dirs(output_dir)

    print(f"データ読み込み中: {data_path}")
    df = load_mind_monitor_csv(data_path, quality_filter=True)
    summary_info = format_summary(get_data_summary(df), df)

    print("fNIRSデータ解析中...")
    optics_data = get_optics_data(df)
    fnirs_results = analyze_fnirs(optics_data)
    fnirs_stats_df = generate_fnirs_stats_table(fnirs_results["stats"])

    images = {}

    # fNIRS可視化
    fig_fnirs, _ = plot_fnirs(fnirs_results)
    images["fnirs_panel"] = f"img/fnirs_panel.png"
    fig_fnirs.savefig(img_dir / "fnirs_panel.png", dpi=150, bbox_inches="tight")
    plt.close(fig_fnirs)

    fig_muse, _ = plot_fnirs_muse_style(fnirs_results)
    images["fnirs_muse_style"] = f"img/fnirs_muse_style.png"
    fig_muse.savefig(img_dir / "fnirs_muse_style.png", dpi=150, bbox_inches="tight")
    plt.close(fig_muse)

    respiratory_stats_df = None
    notes = {}

    hr_data = get_heart_rate_data(df)
    if hr_data["heart_rate"].size > 0:
        print("呼吸推定解析中...")
        respiratory_results = analyze_respiratory(hr_data)
        respiratory_stats_df = generate_respiratory_stats_table(
            respiratory_results["stats"]
        )

        fig_resp, _ = plot_respiratory(hr_data, respiratory_results)
        images["resp_timeseries"] = f"img/respiratory_overview.png"
        fig_resp.savefig(img_dir / "respiratory_overview.png", dpi=150, bbox_inches="tight")
        plt.close(fig_resp)

        fig_psd, _ = plot_frequency_spectrum(respiratory_results)
        images["resp_psd"] = f"img/respiratory_psd.png"
        fig_psd.savefig(img_dir / "respiratory_psd.png", dpi=150, bbox_inches="tight")
        plt.close(fig_psd)

        if fnirs_results["time"].shape == respiratory_results["time"].shape:
            notes["同期性"] = "fNIRSと心拍系列のサンプル数が一致しています。"
        else:
            notes["同期性"] = "fNIRSと心拍系列にサンプル差があります。タイムスタンプに注意してください。"

        fig_dashboard, _ = plot_integrated_dashboard(
            fnirs_results, hr_data, respiratory_results
        )
        images["integrated_dashboard"] = f"img/integrated_dashboard.png"
        fig_dashboard.savefig(
            img_dir / "integrated_dashboard.png", dpi=150, bbox_inches="tight"
        )
        plt.close(fig_dashboard)
    else:
        notes["呼吸推定"] = "有効な心拍データがなかったため呼吸推定をスキップしました。"

    generate_markdown_report(
        data_path=data_path,
        output_dir=output_dir,
        summary_info=summary_info,
        fnirs_stats_df=fnirs_stats_df,
        respiratory_stats_df=respiratory_stats_df,
        images=images,
        notes=notes,
    )


if __name__ == "__main__":
    main()
