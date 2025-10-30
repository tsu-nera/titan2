# Muse S (Athena) Technical Specifications

## Overview
Muse S (Athena) is a multi-sensor EEG headband designed for meditation, sleep tracking, and neurofeedback applications.

---

## Physical Specifications

### Size and Dimensions
- **Size Range**: 43 - 63cm
- **Module Dimensions**: Approx. 6 × 3 × 1.5 cm
- **Headband**:
  - Adjustable length: Approx. 48-63 cm
  - Width: Approx. 3.25 cm
- **Weight**: Approx. 41g

### Materials
- **Pod**: Polycarbonate plastic with soft-touch paint, magnets, glue
- **Soft Band**:
  - Opal (Light): 79.7% Cotton / 13.5% Polyester / 6.8% Spandex
  - Carbon (Dark): 22.4% Rayon / 73.1% Polyester / 4.5% Spandex
- **Electrodes**: 20% silver content, 80% polyamide fabric (nylon) (Upgraded)

---

## EEG Specifications

### Channels and Electrodes
- **EEG Channels**: 4 EEG channels + 4 amplified Aux channels
- **Sample Rate**: 256 Hz
- **Sample Resolution**: 14 bits / sample (Upgraded)
- **Reference Electrode Position**: FPz (CMS/DRL)
- **Channel Electrode Position**: TP9, AF7, AF8, TP10 (dry)
- **EEG Electrode Materials**: Silver thread fabric (dry) (Upgraded)

### Aux Channel Connection
- **Input Range**: 725µV AC signal (1.45mVp-p) with 1.45V DC offset
- **Note**: Aux channels are amplified like all other EEG channels

---

## Additional Sensors

### Accelerometer
- **Type**: Three-axis
- **Sample Rate**: 52 Hz
- **Resolution**: 16-bit
- **Range**: ±2G

### Gyroscope (New)
- **Type**: Three-axis
- **Sample Rate**: 52 Hz
- **Resolution**: 16-bit
- **Range**: ±250 dps

### PPG Sensor (Upgraded)
- **Wavelengths**: Triple wavelength
  - IR: 850nm
  - Near-IR: 730nm
  - Red: 660nm
- **Sample Rate**: 64 Hz
- **Resolution**: 20-bit

### fNIRS Sensor (New)
- **Type**: 5-optode bilateral frontal cortex hemodynamics
- **Sample Rate**: 64 Hz
- **Resolution**: 20-bit

---

## Connectivity and Power

### Wireless Connection
- **Bluetooth**: BLE 5.3, 2.4 GHz (Upgraded)
- **Charging Port**: USB-C (Upgraded)

### Battery
- **Type**: 150mAh Li-ion
- **Charge Time**: 3 hours
- **Usage Time**: Up to 10 hours

---

## Software Compatibility

### Muse App
- **iOS**: Apple iOS 15 or higher
- **Android**: Android 8 or higher
  - **Note**: Huawei devices not supported

---

## Upgrade Notes

The following features have been upgraded or newly added in the Muse S (Athena) model:

- **Upgraded**: Wireless Connection (BLE 5.3)
- **Upgraded**: Charging Port (USB-C)
- **Upgraded**: Sample Resolution (14 bits/sample)
- **Upgraded**: EEG Electrode Materials (Silver thread fabric)
- **Upgraded**: PPG Sensor (Triple wavelength, 20-bit resolution)
- **Upgraded**: Materials (Electrode composition)
- **New**: Gyroscope
- **New**: fNIRS Sensor

---

## Mind Monitor CSV Data Availability

The following sensor data from Muse S Athena can be accessed via Mind Monitor CSV export:

### ✅ Fully Available
- **EEG Signals**: All 4 channels (TP9, AF7, AF8, TP10) with frequency bands (Delta, Theta, Alpha, Beta, Gamma)
- **RAW EEG**: Unfiltered waveform data at 256 Hz
- **Accelerometer**: 3-axis motion data at 52 Hz
- **Gyroscope**: 3-axis rotation data at 52 Hz
- **PPG/fNIRS**: 16 optical channels (Optics1-16) at 64 Hz
  - Wavelengths: 730nm (Near-IR), 850nm (IR), 660nm (Red), Ambient
  - Configuration: Left(inner/outer) and Right(inner/outer) × wavelengths
- **Heart Rate**: Calculated BPM from PPG data
- **Signal Quality**: HSI (Horseshoe Indicator) for each electrode
- **Battery Level**: Real-time percentage
- **Event Markers**: Blinks, jaw clenches, device connection events

### ⚠️ Partially Available
- **Aux Channels**: 4 additional channels available if external sensors are connected via USB

### ❌ Hardware Specifications Only (Not in CSV)
- Sample resolution (14-bit EEG, 20-bit PPG)
- Bluetooth specifications
- Physical materials and dimensions
- Battery capacity

For detailed CSV column specifications, see [MIND_MONITOR_CSV_SPECIFICATION.md](MIND_MONITOR_CSV_SPECIFICATION.md).

---

## References

- Official Muse S Product Page: [InteraXon Inc.](https://choosemuse.com/)
- Mind Monitor App: [mind-monitor.com](https://mind-monitor.com/)
- Last Updated: 2025-10-26
