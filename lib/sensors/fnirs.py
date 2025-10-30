"""
fNIRS（functional Near-Infrared Spectroscopy）センサー解析ライブラリ
Modified Beer-Lambert LawによるHbO/HbR計算

fNIRSセンサーによる近赤外光計測データから脳血流を解析します。
"""

import numpy as np


# Modified Beer-Lambert Lawのパラメータ
EXTINCTION_COEF = {
    730: {'HbO': 1.4866, 'HbR': 3.8437},  # 730nm
    850: {'HbO': 2.5264, 'HbR': 1.7989},  # 850nm
}

# Differential Pathlength Factor (前頭葉・成人)
DPF = 6.0

# ソース-ディテクタ間距離 (cm)
SOURCE_DETECTOR_DISTANCE = 3.0

# Muse App準拠のスケール調整係数
SCALE_FACTOR = 10000.0


def calculate_hbo_hbr(optics_730nm, optics_850nm, baseline_duration=10, sampling_rate=64):
    """
    Modified Beer-Lambert Lawを使ってHbOとHbRを計算

    Parameters
    ----------
    optics_730nm : np.ndarray
        730nmの光強度 (µA)
    optics_850nm : np.ndarray
        850nmの光強度 (µA)
    baseline_duration : float
        ベースライン期間 (秒)
    sampling_rate : float
        サンプリングレート (Hz)

    Returns
    -------
    hbo : np.ndarray
        酸素化ヘモグロビン濃度変化 (µM)
    hbr : np.ndarray
        脱酸素化ヘモグロビン濃度変化 (µM)
    """
    # ベースライン計算用のサンプル数
    baseline_samples = int(baseline_duration * sampling_rate)

    # 光学密度変化 (ΔOD) を計算
    baseline_730 = np.mean(optics_730nm[:baseline_samples])
    baseline_850 = np.mean(optics_850nm[:baseline_samples])

    delta_od_730 = -np.log10(optics_730nm / baseline_730)
    delta_od_850 = -np.log10(optics_850nm / baseline_850)

    # 消衰係数マトリックス
    eps_matrix = np.array([
        [EXTINCTION_COEF[730]['HbO'], EXTINCTION_COEF[730]['HbR']],
        [EXTINCTION_COEF[850]['HbO'], EXTINCTION_COEF[850]['HbR']]
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


def analyze_fnirs(optics_data):
    """
    左右半球のfNIRS解析を実行

    Parameters
    ----------
    optics_data : dict
        get_optics_data()の戻り値
        {
            'left_730': np.ndarray,
            'left_850': np.ndarray,
            'right_730': np.ndarray,
            'right_850': np.ndarray,
            'time': np.ndarray
        }

    Returns
    -------
    fnirs_results : dict
        {
            'left_hbo': np.ndarray,
            'left_hbr': np.ndarray,
            'right_hbo': np.ndarray,
            'right_hbr': np.ndarray,
            'time': np.ndarray,
            'stats': dict
        }
    """
    # 左半球
    left_hbo, left_hbr = calculate_hbo_hbr(
        optics_data['left_730'],
        optics_data['left_850']
    )

    # 右半球
    right_hbo, right_hbr = calculate_hbo_hbr(
        optics_data['right_730'],
        optics_data['right_850']
    )

    # 統計情報
    stats = {
        'left': {
            'hbo_mean': np.mean(left_hbo),
            'hbo_std': np.std(left_hbo),
            'hbo_min': np.min(left_hbo),
            'hbo_max': np.max(left_hbo),
            'hbr_mean': np.mean(left_hbr),
            'hbr_std': np.std(left_hbr),
            'hbr_min': np.min(left_hbr),
            'hbr_max': np.max(left_hbr),
        },
        'right': {
            'hbo_mean': np.mean(right_hbo),
            'hbo_std': np.std(right_hbo),
            'hbo_min': np.min(right_hbo),
            'hbo_max': np.max(right_hbo),
            'hbr_mean': np.mean(right_hbr),
            'hbr_std': np.std(right_hbr),
            'hbr_min': np.min(right_hbr),
            'hbr_max': np.max(right_hbr),
        }
    }

    return {
        'left_hbo': left_hbo,
        'left_hbr': left_hbr,
        'right_hbo': right_hbo,
        'right_hbr': right_hbr,
        'time': optics_data['time'],
        'stats': stats
    }
