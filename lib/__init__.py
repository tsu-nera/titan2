"""
Mind Monitor Analysis Library
"""

from .data_loader import (
    load_mind_monitor_csv,
    get_optics_data,
    get_heart_rate_data,
    get_data_summary
)

from .fnirs import (
    calculate_hbo_hbr,
    analyze_fnirs
)

from .respiratory import (
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

__all__ = [
    # data_loader
    'load_mind_monitor_csv',
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
]
