"""
EEG解析の定数定義
"""

# 周波数バンド定義（Hz）
# (low_freq, high_freq, color)
FREQ_BANDS = {
    'Delta': (0.5, 4, 'purple'),
    'Theta': (4, 8, 'blue'),
    'Alpha': (8, 13, 'green'),
    'Beta': (13, 30, 'orange'),
    'Gamma': (30, 50, 'red')
}

# デフォルトサンプリングレート（Hz）
DEFAULT_SFREQ = 256.0
