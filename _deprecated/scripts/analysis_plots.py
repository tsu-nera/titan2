from __future__ import annotations

import math
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_PATH = Path('/mnt/g/マイドライブ/Muse/mindMonitor_2025-10-09--16-30-38_8375455762917540456.csv')
OUTPUT_DIR = Path('data/plots')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print(f'Reading {DATA_PATH}')
df = pd.read_csv(DATA_PATH)
df['TimeStamp'] = pd.to_datetime(df['TimeStamp'], errors='coerce')
df = df.dropna(subset=['TimeStamp']).sort_values('TimeStamp').reset_index(drop=True)

# Remove channels that are constant zero (e.g. TP10 on this run)
def drop_zero_columns(prefix: str) -> list[str]:
    cols = [c for c in df.columns if c.startswith(prefix)]
    keep = []
    for col in cols:
        values = pd.to_numeric(df[col], errors='coerce')
        if not np.allclose(values.fillna(0), 0.0):
            keep.append(col)
    return keep

bands = ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']
band_cols: dict[str, list[str]] = {}
for band in bands:
    cols = drop_zero_columns(f'{band}_')
    if cols:
        band_cols[band] = cols

rolling_window = 5
rolling_kwargs = dict(window=rolling_window, min_periods=1)

band_mean_df = pd.DataFrame({'TimeStamp': df['TimeStamp']})
for band, cols in band_cols.items():
    numeric = df[cols].apply(pd.to_numeric, errors='coerce')
    band_mean = numeric.mean(axis=1)
    band_mean_df[band] = band_mean.rolling(**rolling_kwargs).mean()

fig, ax = plt.subplots(figsize=(10, 5))
for band in bands:
    if band in band_mean_df:
        ax.plot(band_mean_df['TimeStamp'], band_mean_df[band], label=band)

ax.set_title('Muse EEG Band Power (rolling mean)')
ax.set_xlabel('Time')
ax.set_ylabel('Relative power (a.u.)')
ax.legend(loc='upper right')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
ax.grid(True, alpha=0.3)
fig.autofmt_xdate()
fig.tight_layout()
figure_path = OUTPUT_DIR / 'band_power_timeseries.png'
fig.savefig(figure_path, dpi=200)
plt.close(fig)
print(f'Saved {figure_path}')

# Alpha/Theta and Beta/Alpha ratios (averaged over electrodes)
ratio_df = pd.DataFrame({'TimeStamp': df['TimeStamp']})
for ratio_name, num_band, den_band in [
    ('Alpha/Theta', 'Alpha', 'Theta'),
    ('Beta/Alpha', 'Beta', 'Alpha'),
]:
    num_cols = band_cols.get(num_band, [])
    den_cols = band_cols.get(den_band, [])
    if not num_cols or not den_cols:
        continue
    ratios = []
    for num_col in num_cols:
        electrode = num_col.split('_', 1)[1]
        den_col = f'{den_band}_{electrode}'
        if den_col in df:
            num_vals = pd.to_numeric(df[num_col], errors='coerce')
            den_vals = pd.to_numeric(df[den_col], errors='coerce')
            ratio = (num_vals / den_vals).replace([np.inf, -np.inf], np.nan)
            ratios.append(ratio)
    if ratios:
        ratio_df[ratio_name] = pd.concat(ratios, axis=1).mean(axis=1)

if len(ratio_df.columns) > 1:
    fig, ax = plt.subplots(figsize=(10, 4))
    for col in ratio_df.columns[1:]:
        ax.plot(ratio_df['TimeStamp'], ratio_df[col].rolling(**rolling_kwargs).median(), label=col)
    ax.set_title('Band Power Ratios (rolling median)')
    ax.set_xlabel('Time')
    ax.set_ylabel('Ratio')
    ax.set_ylim(bottom=-1, top=3)
    ax.axhline(1.0, color='grey', linestyle='--', linewidth=0.8)
    ax.legend(loc='upper right')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    figure_path = OUTPUT_DIR / 'band_ratio_timeseries.png'
    fig.savefig(figure_path, dpi=200)
    plt.close(fig)
    print(f'Saved {figure_path}')

# Blink events overlay on Alpha power (if available)
if 'Alpha' in band_mean_df:
    alpha_series = band_mean_df['Alpha']
    blink_mask = df['Elements'].fillna('').str.contains('blink')
    blink_times = df.loc[blink_mask, 'TimeStamp']

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df['TimeStamp'], alpha_series, label='Alpha')
    ymin, ymax = math.floor(alpha_series.min()), math.ceil(alpha_series.max())
    for bt in blink_times:
        ax.axvline(bt, color='tomato', alpha=0.2)
    ax.set_title('Alpha Power with Blink Events')
    ax.set_xlabel('Time')
    ax.set_ylabel('Alpha (a.u.)')
    ax.set_ylim(ymin, ymax if ymax > ymin else ymin + 1)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    figure_path = OUTPUT_DIR / 'alpha_with_blinks.png'
    fig.savefig(figure_path, dpi=200)
    plt.close(fig)
    print(f'Saved {figure_path}')

# Headband fit & battery trend
if {'HSI_TP9', 'HSI_AF7', 'HSI_AF8', 'HSI_TP10'} & set(df.columns):
    hsi_cols = [c for c in ['HSI_TP9', 'HSI_AF7', 'HSI_AF8', 'HSI_TP10'] if c in df]
    hsi_df = df[['TimeStamp'] + hsi_cols].set_index('TimeStamp').rolling(**rolling_kwargs).median()
    fig, ax = plt.subplots(figsize=(10, 4))
    hsi_df.plot(ax=ax)
    ax.set_title('Headband Signal Indicator (HSI)')
    ax.set_xlabel('Time')
    ax.set_ylabel('HSI level (1-4)')
    ax.set_ylim(0, 4.2)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    fig.autofmt_xdate()
    fig.tight_layout()
    figure_path = OUTPUT_DIR / 'hsi_timeseries.png'
    fig.savefig(figure_path, dpi=200)
    plt.close(fig)
    print(f'Saved {figure_path}')

if 'Battery' in df.columns:
    battery = pd.to_numeric(df['Battery'], errors='coerce').rolling(**rolling_kwargs).mean()
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(df['TimeStamp'], battery)
    ax.set_title('Battery Level Over Time')
    ax.set_xlabel('Time')
    ax.set_ylabel('Battery %')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    figure_path = OUTPUT_DIR / 'battery_timeseries.png'
    fig.savefig(figure_path, dpi=200)
    plt.close(fig)
    print(f'Saved {figure_path}')

print('Done')
