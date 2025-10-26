from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Muse MindMonitorのOptics列からPVD信号を生成し、周波数特性を解析します。",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("data/samples/mindMonitor_2025-10-09--16-30-38_8375455762917540456.csv"),
        help="解析対象のCSVファイルパス",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/plots/pvd_frequency.png"),
        help="出力するグラフ画像の保存先パス",
    )
    parser.add_argument(
        "--max-freq",
        type=float,
        default=2.0,
        help="プロットする最大周波数[Hz]",
    )
    return parser.parse_args()


def load_dataframe(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    if "TimeStamp" not in df.columns:
        raise ValueError("TimeStamp列が存在しません。")
    df["TimeStamp"] = pd.to_datetime(df["TimeStamp"], errors="coerce")
    df = df.dropna(subset=["TimeStamp"]).sort_values("TimeStamp").reset_index(drop=True)
    return df


def extract_pvd_series(df: pd.DataFrame) -> pd.Series:
    optics_cols = [col for col in df.columns if col.startswith("Optics")]
    if not optics_cols:
        raise ValueError("Opticsで始まる列が見つからないためPVDを算出できません。")

    optics_numeric = df[optics_cols].apply(pd.to_numeric, errors="coerce")
    pvd_values = optics_numeric.median(axis=1)

    pvd_ts = pd.Series(pvd_values.values, index=df["TimeStamp"])
    pvd_ts = pvd_ts.sort_index()
    pvd_ts = pvd_ts.interpolate(method="time").dropna()
    pvd_ts = pvd_ts.groupby(pvd_ts.index).mean()

    if len(pvd_ts) < 16:
        raise ValueError("データ点が少なすぎるため周波数解析ができません。(16点未満)")

    return pvd_ts


def compute_fft(pvd_ts: pd.Series) -> tuple[np.ndarray, np.ndarray, float]:
    diffs = pvd_ts.index.to_series().diff().dropna()
    if diffs.empty:
        raise ValueError("サンプリング間隔を算出できませんでした。")

    dt = diffs.median()
    dt_seconds = dt.total_seconds()
    if dt_seconds is None or dt_seconds <= 0:
        raise ValueError("サンプリング間隔が0以下になりました。データを確認してください。")

    demeaned = pvd_ts - pvd_ts.mean()
    window = np.hanning(len(demeaned))
    fft_vals = np.fft.rfft(demeaned.values * window)
    freqs = np.fft.rfftfreq(len(demeaned), d=dt_seconds)
    amplitude = np.abs(fft_vals)
    return freqs, amplitude, dt_seconds


def plot_frequency_spectrum(
    freqs: np.ndarray,
    amplitude: np.ndarray,
    output_path: Path,
    max_freq: float,
    sample_rate: float,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(freqs, amplitude, color="midnightblue")
    ax.set_xlim(0, max_freq)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Amplitude (a.u.)")
    ax.set_title(f"PVD Frequency Spectrum (fs ≈ {sample_rate:.3f} Hz)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)



def main() -> None:
    args = parse_args()

    df = load_dataframe(args.csv)
    pvd_ts = extract_pvd_series(df)
    freqs, amplitude, dt_seconds = compute_fft(pvd_ts)
    sample_rate = 1.0 / dt_seconds if dt_seconds > 0 else float("nan")

    plot_frequency_spectrum(freqs, amplitude, args.output, args.max_freq, sample_rate)

    dominant_idx = int(np.argmax(amplitude[1:])) + 1 if len(amplitude) > 1 else 0
    dominant_freq = freqs[dominant_idx] if dominant_idx < len(freqs) else 0.0
    print(f"Saved spectrum to {args.output}")
    print(f"Data points: {len(pvd_ts)}, dt ≈ {dt_seconds:.3f} s, fs ≈ {sample_rate:.3f} Hz")
    if dominant_idx:
        print(f"Dominant frequency ≈ {dominant_freq:.3f} Hz (excluding DC)")


if __name__ == "__main__":
    main()
