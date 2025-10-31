"""
Mind Monitor Analysis Library
"""

from .loaders import (
    load_mind_monitor_csv,
    get_eeg_data,
    get_optics_data,
    get_heart_rate_data,
    get_data_summary
)

from .sensors.fnirs import (
    calculate_hbo_hbr,
    analyze_fnirs
)

from .sensors.ppg import (
    estimate_rr_intervals,
    estimate_respiratory_rate_welch,
    estimate_respiratory_rate_fft,
    analyze_respiratory
)

from .visualization import (
    plot_fnirs,
    plot_fnirs_muse_style,
    plot_respiratory,
    plot_frequency_spectrum,
    plot_integrated_dashboard
)

from .sensors.eeg import (
    calculate_band_statistics,
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
    FREQ_BANDS,
    FrontalThetaResult,
    calculate_frontal_theta,
    plot_frontal_theta,
)

from .eeg import (
    SegmentAnalysisResult,
    calculate_segment_analysis,
    plot_segment_comparison,
)

__all__ = [
    # loaders
    'load_mind_monitor_csv',
    'get_eeg_data',
    'get_optics_data',
    'get_heart_rate_data',
    'get_data_summary',
    # fnirs
    'calculate_hbo_hbr',
    'analyze_fnirs',
    # respiratory
    'estimate_rr_intervals',
    'estimate_respiratory_rate_welch',
    'estimate_respiratory_rate_fft',
    'analyze_respiratory',
    # visualization
    'plot_fnirs',
    'plot_fnirs_muse_style',
    'plot_respiratory',
    'plot_frequency_spectrum',
    'plot_integrated_dashboard',
    # eeg
    'get_eeg_data',
    'calculate_band_statistics',
    'prepare_mne_raw',
    'filter_eeg_quality',
    'calculate_psd',
    'calculate_spectrogram',
    'calculate_band_ratios',
    'calculate_paf',
    'calculate_paf_time_evolution',
    'plot_band_power_time_series',
    'plot_psd',
    'plot_psd_time_series',
    'plot_spectrogram',
    'plot_band_ratios',
    'plot_paf',
    'plot_paf_time_evolution',
    'get_psd_peak_frequencies',
    'setup_japanese_font',
    'FREQ_BANDS',
    'FrontalThetaResult',
    'calculate_frontal_theta',
    'plot_frontal_theta',
    # high-level eeg utilities
    'SegmentAnalysisResult',
    'calculate_segment_analysis',
    'plot_segment_comparison',
]
