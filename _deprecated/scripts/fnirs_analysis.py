#!/usr/bin/env python3
"""
Mind Monitor fNIRS Analysis Script
Muse S (4-channel configuration) のOpticsデータからHbO/HbRを計算して可視化
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Modified Beer-Lambert Lawのパラメータ
# 参考: https://mne.tools/stable/auto_tutorials/preprocessing/70_fnirs_processing.html
WAVELENGTHS = {
    '730nm': 730,  # Near-IR
    '850nm': 850,  # IR
}

# 消衰係数 (extinction coefficients) [cm^-1 / (mM mm)]
# HbO (oxygenated hemoglobin) と HbR (deoxygenated hemoglobin)
EXTINCTION_COEF = {
    730: {'HbO': 1.4866, 'HbR': 3.8437},  # 730nm
    850: {'HbO': 2.5264, 'HbR': 1.7989},  # 850nm
}

# Differential Pathlength Factor (DPF)
# 前頭葉の典型的な値 (成人)
DPF = 6.0

# ソース-ディテクタ間距離 (cm) - Muse Sの推定値
SOURCE_DETECTOR_DISTANCE = 3.0  # cm

# スケール調整係数
# Muse Appの表示範囲（-7/+7 µM）に合わせるための係数
SCALE_FACTOR = 10000.0  # 実験的に決定（Muse App準拠）


def load_mind_monitor_csv(csv_path):
    """
    Mind Monitor CSVファイルを読み込む

    Parameters
    ----------
    csv_path : str or Path
        CSVファイルのパス

    Returns
    -------
    df : pd.DataFrame
        読み込んだデータフレーム
    """
    df = pd.read_csv(csv_path)

    # タイムスタンプをDatetime型に変換
    df['TimeStamp'] = pd.to_datetime(df['TimeStamp'])

    # 相対時間 (秒) を計算
    df['Time_sec'] = (df['TimeStamp'] - df['TimeStamp'].iloc[0]).dt.total_seconds()

    return df


def calculate_hbo_hbr(optics_730nm, optics_850nm):
    """
    Modified Beer-Lambert Lawを使ってHbOとHbRを計算

    Parameters
    ----------
    optics_730nm : np.ndarray
        730nmの光強度 (µA)
    optics_850nm : np.ndarray
        850nmの光強度 (µA)

    Returns
    -------
    hbo : np.ndarray
        酸素化ヘモグロビン濃度変化 (µM)
    hbr : np.ndarray
        脱酸素化ヘモグロビン濃度変化 (µM)
    """
    # 光学密度変化 (ΔOD) を計算
    # ΔOD = -log10(I/I0) ≈ -log10(I) + log10(I0)
    # ベースラインとして最初の10秒の平均を使用
    baseline_730 = np.mean(optics_730nm[:640])  # 64Hz × 10秒
    baseline_850 = np.mean(optics_850nm[:640])

    delta_od_730 = -np.log10(optics_730nm / baseline_730)
    delta_od_850 = -np.log10(optics_850nm / baseline_850)

    # 消衰係数マトリックス
    eps_hbo_730 = EXTINCTION_COEF[730]['HbO']
    eps_hbr_730 = EXTINCTION_COEF[730]['HbR']
    eps_hbo_850 = EXTINCTION_COEF[850]['HbO']
    eps_hbr_850 = EXTINCTION_COEF[850]['HbR']

    # Modified Beer-Lambert Law:
    # ΔOD(λ) = (ε_HbO(λ) * Δ[HbO] + ε_HbR(λ) * Δ[HbR]) * DPF * d
    #
    # 2波長の連立方程式を解く:
    # [ΔOD_730]   [ε_HbO(730)  ε_HbR(730)]   [Δ[HbO]]
    # [ΔOD_850] = [ε_HbO(850)  ε_HbR(850)] * [Δ[HbR]] * DPF * d

    # 逆行列を使って解く
    eps_matrix = np.array([
        [eps_hbo_730, eps_hbr_730],
        [eps_hbo_850, eps_hbr_850]
    ])

    eps_inv = np.linalg.inv(eps_matrix)

    # 各時点でHbO, HbRを計算
    hbo = np.zeros_like(delta_od_730)
    hbr = np.zeros_like(delta_od_730)

    for i in range(len(delta_od_730)):
        delta_od = np.array([delta_od_730[i], delta_od_850[i]])
        concentrations = eps_inv @ delta_od / (DPF * SOURCE_DETECTOR_DISTANCE)
        hbo[i] = concentrations[0]
        hbr[i] = concentrations[1]

    # Muse App準拠のスケールに調整
    hbo = hbo * SCALE_FACTOR
    hbr = hbr * SCALE_FACTOR

    return hbo, hbr


def plot_fnirs_timeseries(time, left_hbo, left_hbr, right_hbo, right_hbr, output_path=None):
    """
    fNIRS時系列データを4つのサブプロットで可視化

    Parameters
    ----------
    time : np.ndarray
        時間軸 (秒)
    left_hbo : np.ndarray
        左前頭葉のHbO
    left_hbr : np.ndarray
        左前頭葉のHbR
    right_hbo : np.ndarray
        右前頭葉のHbO
    right_hbr : np.ndarray
        右前頭葉のHbR
    output_path : str or Path, optional
        保存先パス
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('fNIRS Analysis: HbO/HbR Concentration Changes', fontsize=16, fontweight='bold')

    # Left HbO
    axes[0, 0].plot(time, left_hbo, color='red', linewidth=1.5)
    axes[0, 0].set_title('Left Hemisphere - HbO (Oxygenated)', fontsize=12, fontweight='bold')
    axes[0, 0].set_xlabel('Time (seconds)')
    axes[0, 0].set_ylabel('Δ[HbO] (µM)')
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].axhline(y=0, color='black', linestyle='--', linewidth=0.8, alpha=0.5)

    # Left HbR
    axes[1, 0].plot(time, left_hbr, color='blue', linewidth=1.5)
    axes[1, 0].set_title('Left Hemisphere - HbR (Deoxygenated)', fontsize=12, fontweight='bold')
    axes[1, 0].set_xlabel('Time (seconds)')
    axes[1, 0].set_ylabel('Δ[HbR] (µM)')
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].axhline(y=0, color='black', linestyle='--', linewidth=0.8, alpha=0.5)

    # Right HbO
    axes[0, 1].plot(time, right_hbo, color='red', linewidth=1.5)
    axes[0, 1].set_title('Right Hemisphere - HbO (Oxygenated)', fontsize=12, fontweight='bold')
    axes[0, 1].set_xlabel('Time (seconds)')
    axes[0, 1].set_ylabel('Δ[HbO] (µM)')
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].axhline(y=0, color='black', linestyle='--', linewidth=0.8, alpha=0.5)

    # Right HbR
    axes[1, 1].plot(time, right_hbr, color='blue', linewidth=1.5)
    axes[1, 1].set_title('Right Hemisphere - HbR (Deoxygenated)', fontsize=12, fontweight='bold')
    axes[1, 1].set_xlabel('Time (seconds)')
    axes[1, 1].set_ylabel('Δ[HbR] (µM)')
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].axhline(y=0, color='black', linestyle='--', linewidth=0.8, alpha=0.5)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"グラフを保存しました: {output_path}")

    plt.show()


def main():
    """メイン処理"""
    # データファイルパス
    csv_path = Path("data/samples/mindMonitor_2025-10-26--08-32-20_1403458594426768660.csv")

    if not csv_path.exists():
        print(f"エラー: ファイルが見つかりません: {csv_path}")
        return

    print(f"データ読み込み中: {csv_path}")
    df = load_mind_monitor_csv(csv_path)

    # データ品質チェック
    valid_data = df[df['HeadBandOn'] == 1].copy()
    print(f"総データポイント数: {len(df)}")
    print(f"有効データポイント数: {len(valid_data)} (HeadBandOn=1)")
    print(f"記録時間: {valid_data['Time_sec'].max():.1f} 秒")

    # Opticsデータを取得 (4チャンネル構成)
    # Optics1: 730nm Left Inner
    # Optics2: 730nm Right Inner
    # Optics3: 850nm Left Inner
    # Optics4: 850nm Right Inner
    time = valid_data['Time_sec'].values

    # 左前頭葉
    left_730 = valid_data['Optics1'].values
    left_850 = valid_data['Optics3'].values

    # 右前頭葉
    right_730 = valid_data['Optics2'].values
    right_850 = valid_data['Optics4'].values

    print("\nOptics データ統計:")
    print(f"  Left 730nm: min={left_730.min():.3f}, max={left_730.max():.3f}, mean={left_730.mean():.3f} µA")
    print(f"  Left 850nm: min={left_850.min():.3f}, max={left_850.max():.3f}, mean={left_850.mean():.3f} µA")
    print(f"  Right 730nm: min={right_730.min():.3f}, max={right_730.max():.3f}, mean={right_730.mean():.3f} µA")
    print(f"  Right 850nm: min={right_850.min():.3f}, max={right_850.max():.3f}, mean={right_850.mean():.3f} µA")

    # HbO/HbR計算
    print("\nHbO/HbR計算中...")
    left_hbo, left_hbr = calculate_hbo_hbr(left_730, left_850)
    right_hbo, right_hbr = calculate_hbo_hbr(right_730, right_850)

    print("HbO/HbR 統計:")
    print(f"  Left HbO: min={left_hbo.min():.3f}, max={left_hbo.max():.3f}, mean={left_hbo.mean():.3f} µM")
    print(f"  Left HbR: min={left_hbr.min():.3f}, max={left_hbr.max():.3f}, mean={left_hbr.mean():.3f} µM")
    print(f"  Right HbO: min={right_hbo.min():.3f}, max={right_hbo.max():.3f}, mean={right_hbo.mean():.3f} µM")
    print(f"  Right HbR: min={right_hbr.min():.3f}, max={right_hbr.max():.3f}, mean={right_hbr.mean():.3f} µM")

    # 可視化
    print("\nグラフ作成中...")
    output_path = Path("output/fnirs_timeseries.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plot_fnirs_timeseries(
        time,
        left_hbo, left_hbr,
        right_hbo, right_hbr,
        output_path=output_path
    )

    print("\n処理完了！")


if __name__ == "__main__":
    main()
