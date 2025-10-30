#!/usr/bin/env python3
"""
サンプリングレートの検証
"""

import numpy as np
from lib import load_mind_monitor_csv, get_heart_rate_data, get_optics_data


def main():
    csv_path = "data/samples/mindMonitor_2025-10-26--08-32-20_1403458594426768660.csv"

    print("=" * 60)
    print("サンプリングレート検証")
    print("=" * 60)

    df = load_mind_monitor_csv(csv_path, quality_filter=True)

    # Opticsデータのサンプリングレート
    optics_data = get_optics_data(df)
    optics_time = optics_data['time']
    optics_diff = np.diff(optics_time)
    optics_sr = 1.0 / np.median(optics_diff)

    print("\n【Opticsデータ（fNIRS/PPG）】")
    print(f"  総データ数: {len(optics_time):,}")
    print(f"  時間差の中央値: {np.median(optics_diff)*1000:.3f} ms")
    print(f"  推定サンプリングレート: {optics_sr:.2f} Hz")
    print(f"  仕様値: 64 Hz")
    print(f"  差異: {abs(optics_sr - 64):.2f} Hz")

    # 心拍数データのサンプリングレート
    hr_data = get_heart_rate_data(df)
    hr_time = hr_data['time']
    hr_diff = np.diff(hr_time)

    # 正の時間差のみでサンプリングレートを計算
    hr_diff_positive = hr_diff[hr_diff > 0]
    hr_sr = 1.0 / np.median(hr_diff)
    hr_sr_positive = 1.0 / np.median(hr_diff_positive) if len(hr_diff_positive) > 0 else 0

    print("\n【心拍数データ】")
    print(f"  総データ数: {len(hr_time):,}")
    print(f"  全時間差の中央値: {np.median(hr_diff)*1000:.3f} ms → {hr_sr:.2f} Hz")
    print(f"  正の時間差のみ: {np.median(hr_diff_positive)*1000:.3f} ms → {hr_sr_positive:.2f} Hz")
    print(f"  時間差の範囲: {hr_diff.min()*1000:.3f} - {hr_diff.max()*1000:.3f} ms")
    print(f"  負の時間差: {(hr_diff < 0).sum():,} / {len(hr_diff):,} ({(hr_diff < 0).sum()/len(hr_diff)*100:.1f}%)")

    # 分布の確認
    print("\n【心拍数データの時間間隔分布】")
    intervals, counts = np.unique(np.round(hr_diff * 1000, 1), return_counts=True)
    top_5 = np.argsort(counts)[-5:][::-1]
    for idx in top_5:
        print(f"  {intervals[idx]:.1f} ms: {counts[idx]:,} 回 ({counts[idx]/len(hr_diff)*100:.1f}%)")

    print("\n" + "=" * 60)
    print("【結論】")
    print("=" * 60)

    if abs(optics_sr - 64) < 1:
        print("✅ Opticsデータは64 Hz仕様通り")
    else:
        print(f"⚠️  Opticsデータは仕様と異なる ({optics_sr:.2f} Hz)")
        print("   → Mind MonitorはEEGと同じ250 Hzで全データを記録している可能性")

    if abs(hr_sr_positive - 250) < 10:
        print(f"✅ 心拍数データは250 Hz相当 (正の時間差から推定: {hr_sr_positive:.2f} Hz)")
        print("   → 仕様値64 Hzは使用不可、推定値を使用")
    else:
        print(f"⚠️  心拍数データのサンプリングレートが不明確")
        print(f"   → 正の時間差から推定: {hr_sr_positive:.2f} Hz")

    print("\n💡 推奨: 仕様値ではなく、実データから推定したサンプリングレートを使用")
    print("=" * 60)


if __name__ == "__main__":
    main()
