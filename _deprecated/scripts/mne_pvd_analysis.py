from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import mne
import numpy as np
import pandas as pd


RAW_PREFIX = "RAW_"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MindMonitorデータをMNEで読み込み、RAW電極のPSDを算出する",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("data/samples/mindMonitor_2025-10-09--16-30-38_8375455762917540456.csv"),
        help="入力CSVパス",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/plots/mne_psd.png"),
        help="PSD図の保存先",
    )
    parser.add_argument(
        "--max-freq",
        type=float,
        default=50.0,
        help="プロットで表示する最大周波数(Hz)",
    )
    return parser.parse_args()


def load_raw_channels(df: pd.DataFrame) -> list[str]:
    raw_cols = [c for c in df.columns if c.startswith(RAW_PREFIX)]
    if not raw_cols:
        raise ValueError("RAW_で始まる列が見つかりません。MindMonitorのRAWチャネルが必要です。")
    return raw_cols


def preprocess_dataframe(df: pd.DataFrame, raw_cols: list[str]) -> pd.DataFrame:
    if "TimeStamp" not in df.columns:
        raise ValueError("TimeStamp列が存在しません。")

    df = df.dropna(subset=["TimeStamp"]).sort_values("TimeStamp").reset_index(drop=True)
    df["TimeStamp"] = pd.to_datetime(df["TimeStamp"], errors="coerce")
    df = df.dropna(subset=["TimeStamp"])

    numeric = df[raw_cols].apply(pd.to_numeric, errors="coerce")
    frame = pd.concat([df["TimeStamp"], numeric], axis=1)
    frame = frame.set_index("TimeStamp")

    # 重複タイムスタンプは平均化
    frame = frame.groupby(level=0).mean()

    # 時間補間で欠損値を埋め、さらに先読み・後読み
    frame = frame.interpolate(method="time").ffill().bfill()

    if frame.isna().any().any():
        raise ValueError("欠損値が残っています。入力データを確認してください。")

    return frame


def compute_sampling_rate(index: pd.Index) -> float:
    diffs = index.to_series().diff().dropna()
    if diffs.empty:
        raise ValueError("サンプリング間隔が算出できません。")
    dt = diffs.median()
    dt_seconds = dt.total_seconds()
    if dt_seconds <= 0:
        raise ValueError("サンプリング間隔が0以下です。")
    return 1.0 / dt_seconds


def create_raw_array(frame: pd.DataFrame, sfreq: float) -> mne.io.RawArray:
    ch_names = list(frame.columns)
    ch_types = ["eeg"] * len(ch_names)
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types)

    # MindMonitorのRAW値はおそらくμVスケールなのでVに変換
    data = frame.to_numpy().T * 1e-6

    raw = mne.io.RawArray(data, info, copy="auto")

    try:
        raw.set_montage("standard_1020", match_case=False, on_missing="ignore")
    except OSError:
        # ローカルファイルが見つからない場合は無視
        pass

    # DCドリフト軽減
    if raw.info["sfreq"] > 2.0:
        raw = raw.filter(l_freq=1.0, h_freq=None, fir_design="firwin", verbose=False)
    else:
        print("Sampling rate too low for 1 Hz high-pass filter; skipping filtering.")
    return raw


def compute_and_plot_psd(raw: mne.io.Raw, output: Path, max_freq: float) -> None:
    nyquist = raw.info["sfreq"] / 2.0
    fmax = min(max_freq, max(nyquist - 1e-6, nyquist * 0.9))
    if fmax <= 0:
        raise ValueError("サンプリング周波数が低すぎるためPSDを計算できません。")

    n_fft = min(256, len(raw.times))
    spectrum = raw.compute_psd(
        method="welch",
        n_fft=n_fft,
        n_overlap=0,
        fmax=fmax,
        verbose=False,
    )
    freqs = spectrum.freqs
    psds = spectrum.get_data()
    psds = np.maximum(psds, np.finfo(float).eps)

    # V^2/Hz を μV^2/Hz へ変換（1 V = 1e6 μV）
    psds_uv = psds * 1e12

    output.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 4))
    for ch_name, psd in zip(raw.ch_names, psds_uv):
        ax.plot(freqs, psd, label=ch_name)

    ax.set_xlim(0, min(max_freq, freqs.max()))
    ax.set_yscale("log")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("PSD (μV²/Hz)")
    ax.set_title("Muse RAW PSD (Welch)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(output, dpi=200)
    plt.close(fig)

    print(f"Saved PSD figure to {output}")
    print(f"Frequency range: 0 - {freqs.max():.2f} Hz (plot limited to {min(max_freq, freqs.max()):.2f} Hz)")



def main() -> None:
    args = parse_args()

    df = pd.read_csv(args.csv)
    raw_cols = load_raw_channels(df)
    frame = preprocess_dataframe(df, raw_cols)
    sfreq = compute_sampling_rate(frame.index)

    print(f"Detected channels: {raw_cols}")
    print(f"Estimated sampling rate: {sfreq:.3f} Hz (samples: {len(frame)})")

    raw = create_raw_array(frame, sfreq)
    compute_and_plot_psd(raw, args.output, args.max_freq)


if __name__ == "__main__":
    main()
