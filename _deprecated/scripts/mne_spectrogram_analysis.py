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
        description="MindMonitorデータをMNEで読み込み、RAW電極のスペクトログラムを生成する",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("data/samples/mindMonitor_2025-10-15--17-08-15_2188947289907039573.csv"),
        help="入力CSVパス",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/plots/mne_spectrogram.png"),
        help="スペクトログラム図の保存先",
    )
    parser.add_argument(
        "--max-freq",
        type=float,
        default=50.0,
        help="プロットで表示する最大周波数(Hz)",
    )
    parser.add_argument(
        "--channel",
        type=str,
        default="RAW_TP9",
        help="スペクトログラムを表示するチャネル名(例: RAW_TP9)",
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


def compute_and_plot_spectrogram(
    raw: mne.io.Raw,
    output: Path,
    max_freq: float,
    channel: str,
) -> None:
    if channel not in raw.ch_names:
        raise ValueError(f"チャネル '{channel}' が見つかりません。利用可能なチャネル: {raw.ch_names}")

    nyquist = raw.info["sfreq"] / 2.0
    fmax = min(max_freq, max(nyquist - 1e-6, nyquist * 0.9))
    if fmax <= 0:
        raise ValueError("サンプリング周波数が低すぎるためスペクトログラムを計算できません。")

    # 指定チャネルのデータを取得
    ch_idx = raw.ch_names.index(channel)

    # TFRスペクトログラムを計算
    freqs = np.arange(1.0, fmax, 1.0)
    n_cycles = freqs / 2.0  # 周波数の半分のサイクル数

    # Morlet waveletを使用してtime-frequency解析
    # tfr_array_morletは(n_epochs, n_chans, n_times)の形状を期待
    data_3d = raw.get_data()[ch_idx:ch_idx+1, :][np.newaxis, :, :]
    power = mne.time_frequency.tfr_array_morlet(
        data_3d,
        sfreq=raw.info["sfreq"],
        freqs=freqs,
        n_cycles=n_cycles,
        output="power",
        verbose=False,
    )

    # V^2 を μV^2 へ変換
    power_uv = power[0, 0] * 1e12

    output.parent.mkdir(parents=True, exist_ok=True)

    # スペクトログラムをプロット
    fig, ax = plt.subplots(figsize=(12, 6))
    times = raw.times

    # dB変換してプロット
    power_db = 10 * np.log10(power_uv)

    im = ax.pcolormesh(
        times,
        freqs,
        power_db,
        shading="auto",
        cmap="viridis",
    )

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Frequency (Hz)")
    ax.set_title(f"Spectrogram - {channel}")
    ax.set_ylim(0, fmax)

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Power (dB, μV²)")

    fig.tight_layout()
    fig.savefig(output, dpi=200)
    plt.close(fig)

    print(f"Saved spectrogram to {output}")
    print(f"Channel: {channel}")
    print(f"Frequency range: {freqs.min():.2f} - {freqs.max():.2f} Hz")
    print(f"Time range: {times[0]:.2f} - {times[-1]:.2f} s")


def main() -> None:
    args = parse_args()

    df = pd.read_csv(args.csv)
    raw_cols = load_raw_channels(df)
    frame = preprocess_dataframe(df, raw_cols)
    sfreq = compute_sampling_rate(frame.index)

    print(f"Detected channels: {raw_cols}")
    print(f"Estimated sampling rate: {sfreq:.3f} Hz (samples: {len(frame)})")

    raw = create_raw_array(frame, sfreq)
    compute_and_plot_spectrogram(raw, args.output, args.max_freq, args.channel)


if __name__ == "__main__":
    main()
