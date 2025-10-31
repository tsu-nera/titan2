# MUSE EEG データ仕様

このドキュメントは、旧 Muse Developer ドキュメント（2018 年 11 月 5 日時点アーカイブ）に基づき、Muse/Mind Monitor で取得できる生体信号の仕様を整理したものです。

## EEG プリセットとサンプリングレート

| プリセット ID | 分解能 | EEG サンプリングレート | チャンネル構成 |
| --- | --- | --- | --- |
| 10 / 12 / 14 | 10 bit | 220 Hz | TP9, Fp1, Fp2, TP10 |
| AD / AE | 16 bit | 500 Hz | AD: TP9, Fp1, Fp2, TP10 / AE: 上記 + DRL, REF |

## 共通メタデータ

- OSC パス: 各データ種別ごとに `/muse/...` 形式で配信。
- タイムスタンプ付与: `--osc_timestamp` オプション利用時は秒（整数）とマイクロ秒（整数）が追加される。
- プリセット: 接続時に送信する `preset` コマンドで分解能やサンプリングレートを設定。

## EEG データ

- 電極: `TP9`, `AF7`, `AF8`, `TP10` の 4ch。
- 値の種類:
  - `RAW`: 未処理電位（μV）。
  - `ABSOLUTE`: 特定帯域の絶対パワー（log10(μV²/Hz) 換算）。
  - `RELATIVE`: 対象帯域パワーを全帯域パワーで正規化した比率。
  - `SPECTRAL`: 周波数帯域別のスペクトル推定値（μV²/Hz）。
- 周波数帯域: `DELTA (1–4 Hz)`, `THETA (4–8 Hz)`, `ALPHA (7.5–13 Hz)`, `BETA (13–30 Hz)`, `GAMMA (30–44 Hz)`。
- Headband Status Indicator (HSI): 各電極ごとに 0–3 の整数で装着状態を示す（3: 良好）。
- Quantization Level: 圧縮時に用いる除数で、値が大きいほど量子化誤差が増加。
- Dropped Samples: Bluetooth 由来の欠落サンプル数を整数で報告。

## IMU データ

- 加速度計: `ACC_X`, `ACC_Y`, `ACC_Z`（単位 g）。重力方向を含む 3 軸加速度。
- ジャイロスコープ: `GYRO_X`, `GYRO_Y`, `GYRO_Z`（単位 °/s）。ヘッドバンド回転速度。
- サンプリングレート: 50 Hz。
- Dropped Samples: 欠落サンプル数を整数で報告。

## バッテリー情報

- バッテリー電圧: ミリボルト単位。
- バッテリーレベル: 0–100 %。
- チャージング状態: 充電中かどうかを示すブール値。
- 送信間隔: 約 10 秒（0.1 Hz）。
- データ構造: `[残量(百分率×100), fuel_gauge電圧(mV), adc電圧(mV), 温度(℃)]`。
- 電圧範囲: 3000–4200 mV（Fuel Gauge）、3200–4200 mV（ADC）。
- 温度範囲: -40–125 ℃。

## 追加計算値（Muse Elements）

- Raw FFT: 各チャンネル 129 bin のパワースペクトル密度（dB スケール）を 10 Hz で配信。
- 絶対バンドパワー: `DELTA (1–4 Hz)` など 6 帯域の対数スケール値（単位 Bels）。
- 相対バンドパワー: 線形スケールに戻した値を全帯域合計で割った比率（0–1）。
- セッションスコア: 10–90 パーセンタイルを基準に 0–1 へ線形正規化した帯域スコア。
- Low Freqs: 2.5–6.1 Hz を対象とした低周波パワーを追加バンドとして提供。

## ヘッドバンド装着状態

- Touching Forehead: 装着状態を示すブール値。
- Horseshoe: チャンネルごとの装着品質（1=良、2=可、3=不良）。
- Strict Indicator: チャンネルごとの装着品質（0=不良、1=良）。

## マッスルアーチファクト検出

- Blink: 瞬目検出（ブール値、10 Hz）。
- Jaw Clench: 歯噛み検出（ブール値、10 Hz）。

## 実験的指標

- Concentration: γ帯域を主成分とする集中度スコア（0–1、10 Hz）。筋電アーチファクトによる偽陽性が発生しやすい。
- Mellow: α帯域を主成分とするリラクゼーションスコア（0–1、10 Hz）。逐次アップデートされる実験的値。

## DRL/REF データ

- DRL/REF: 基準電極電位を 2 つの float 値で提供。サンプリングレートは EEG と同一。
- レンジ: 約 0–3,300,000 μV。

## 設定情報

- Config メッセージ: JSON ライクな文字列で一括提供。MAC アドレス、サンプリング周波数、フィルタ設定、量子化ビット幅などを含む。
- Version: ハードウェア・ファームウェアバージョンを 10 秒間隔で提供。
- Annotation: イベントマーカー用の文字列フィールド群。
- グローバル設定例: `mac_addr`, `serial_number`, `preset`, `model`。
- EEG 設定例: `eeg_sample_frequency_hz`, `eeg_output_frequency_hz`, `eeg_downsample`, `eeg_channel_layout`, `notch_filter`。
- 加速度設定例: `acc_sample_frequency_hz`, `acc_output_frequency_hz`, `acc_units`, `acc_data_enabled`。
- バッテリ設定例: `battery_data_enabled`, `battery_percent_remaining_interval`。
- エラー設定例: `error_data_enabled`。

## バージョン・アノテーションデータ

- Version: `/muse/version` でファームウェア種別やビルド番号などを 10 秒間隔で提供。
- Annotation: `/muse/annotation` でイベント名や種別、ID を送信。空フィールドも空文字として保持する必要がある。

## 互換性と注意事項

- Mind Monitor は上記フィールド名をおおむね踏襲しているが、アプリバージョンにより追加列（例: `Artifacts` 列）が存在する場合がある。
- `--no-scale` オプション使用時は単位変換前の値が送られ、将来的に仕様変更される可能性がある。
- Quantization Level が大きい場合は精度低下が大きくなるため、解析前に確認すること。
- Dropped Samples が非ゼロの区間は時系列解析時に欠損処理が必要。
- Horseshoe/Strict インジケータ値が悪いチャンネルはフィルタリングまたは除外を推奨。
