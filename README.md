# PPTX Narrator

PowerPoint（`.pptx`）の**発表者ノート**を抽出し、ローカルの AivisSpeech Engine で  
スライド単位の音声と結合音声を生成します。  
(OpenAI APIなどの外部TTSサービスは使用しません。)

## ファイル構成

```text
pptx-narrator/
|-- aivis-data/
|   `-- Models/
|       `-- *.aivmx
|-- compose.yaml
|-- dict/
|   |-- common.yaml
|   |-- autosar.yaml
|   |-- linux.yaml
|   |-- network.yaml
|   |-- company.yaml
|   |-- aivis-user-dict.json  # 自動生成、Git管理外
|   `-- README.md
|-- docker/
|   |-- Dockerfile
|   |-- app/
|   |   |-- generate_audio.py
|   |   |-- generate_dict.py
|   |   `-- requirements.txt
|   |-- corporate-ca-bundle.crt
|   `-- entrypoint
|-- GNUmakefile
|-- sample/
|   `-- introduction_to_autosar.pptx
|-- output/
`-- README.md
```

## 動作環境

- メモリ8GB以上 (GPUを使わないCPU版のため)
- Ubuntu 24.04 LTS 以降 (WSL2環境でも可)
- Docker Engine
- Docker Compose v2

## 事前準備

[AivisHub](https://hub.aivis-project.com/) からライセンスを確認の上、  
`.aivmx` 音声モデルをダウンロードし、`aivis-data/Models/` へ配置してください。

## 使用方法

音声を生成するPowerPointファイルをリポジトリ配下にコピーし、  
リポジトリのルートで以下を実行します。  
※PowerPointファイルはコンテナ内からアクセスするためリポジトリ配下にある必要があります。

1. 環境の構築 (初回のみ)  
   `make setup`
2. 音声モデルの確認  
   `make voices`  
   ダウンロードした音声モデルの話者のスタイルIDが表示されます。  
   ※初回はBERT関連データの取得と初期化に数分かかる場合があります。
3. PowerPointの発表者ノートの抽出 (省略可)  
   `make extract PPTX="sample/introduction_to_autosar.pptx"`  
   ※`output/<PowerPointファイル名(拡張子なし)>/notes/` 配下に発表者ノートがテキスト保存されます。  
   　発話内容を確認することができます。
4. 音声ファイルの生成  
   `make tts PPTX="sample/introduction_to_autosar.pptx" STYLE_ID=<make voicesで確認したスタイルID>`  
   ※`output/<PowerPointファイル名(拡張子なし)>/slides/` 配下にスライド毎の音声ファイル `.mp3` が生成され、  
   　`output/<PowerPointファイル名(拡張子なし)>/narration.mp3` に結合音声が生成されます。

## 制約事項

- ノート内の書式、強調、アニメーション、タイミング情報は使用しません。
- 発表者ノートを単純なテキストとして読みます。
- PowerPointのスライド表示時間とは同期しません。
- 音声モデル自体は同梱しません。
- 読み間違いは、`dict/*.yaml`の読み辞書または原稿表記で調整します。
- `cpu-latest`を使うため、将来のEngine更新でAPI差分が発生する可能性があります。
- 再実行時に古いファイルが残ることがあります。  
  完全に作り直す場合は対象の出力ディレクトリを削除してください。

## 各コマンドの詳細

本環境はDockerコンテナで構築され各種コマンドはコンテナ内で実行されます。  
dockerの起動および内部のコマンドの呼び出しを `make` で行うことができます。  
用意されているコマンドは以下のとおりです。

```bash
make setup                          # コンテナの構築
make launch                         # AivisSpeech Engine(サーバー)の起動
make shutdown                       # AivisSpeech Engine(サーバー)の停止
make restart                        # AivisSpeech Engine(サーバー)の再起動
make voices                         # 利用可能な話者・style_idの表示
make extract PPTX=...               # 発表者ノートだけを抽出
make tts PPTX=...                   # 音声ファイルの生成
make dict                           # 読み辞書を生成し、Engineへ反映
make logs                           # Engineログを追跡
make ps                             # コンテナ状態を表示
make help                           # ヘルプ表示
```

### `make setup`

コンテナの構築をします。

### `make launch` / `make shutdown` / `make restart`

AivisSpeech Engine(サーバー)の起動・停止・再起動をします。

`aivis-data`はホストのバインドマウントなので、停止後もモデルとキャッシュは残ります。


### `make voices`

配置された音声モデルの話者とスタイルを表示します。  
音声ファイル生成の際、`style=` で示された ID (スタイルID) を使用します。

出力例:

```text
style_id=888753760    speaker=話者名    style=ノーマル
```

### `make extract`

PowerPointファイルの発表者ノートをテキストファイルに抽出します。  
音声ファイル生成の前に、抽出結果をレビューできます。

```bash
make extract PPTX=<PowerPointファイル名>
```

抽出結果:

```text
output/introduction_to_autosar/notes/slide-001.txt
output/introduction_to_autosar/notes/slide-002.txt
...
```

尚、`python-pptx` の `has_notes_slide` で既存ノートの有無を確認し、  
`notes_text_frame`から本文を取得します。  
ノートのないスライドは作成されません。

レビューポイントは以下の通り。

- 英字略語の読み
- `AUTOSAR AP`、`ARA`、`SOA`、`SOME/IP`などの専門用語
- 記号、括弧、スラッシュ
- 箇条書きの読み順
- 読み上げ不要なノート

尚、読み方を安定させるには、発表者ノート側を読み上げ用表記へ直す方法が確実です。  
※詳細割愛

### `make tts`

音声ファイルを生成します。  

```bash
make tts PPTX=<PowerPointファイル> STYLE_ID=<スタイルID> TTS_ARGS=<詳細オプション>
```

実行により以下のように生成されます。

```text
output/
└── <PowerPointファイル名(拡張子なし)>/
    ├── notes/
    ├── slides/
    │   ├── slide-001.mp3
    │   ├── slide-002.mp3
    │   └── ...
    ├── manifest.json
    └── narration.mp3
```

`TTS_ARGS` オプションで詳細な機能指定ができます。  
主なオプションは以下の通り。

```text
--list-voices            話者・スタイル一覧
--extract-only           ノート抽出のみ
--style-id ID            使用するスタイルID
--speed VALUE            話速倍率（標準 1.0）
--pitch VALUE            音高調整（標準 0.0）
--intonation VALUE       抑揚倍率（標準 1.0）
--volume VALUE           音量倍率（標準 1.0）
--pre-phoneme-length S   文頭無音秒
--post-phoneme-length S  文末無音秒
--slide-gap S            結合時のスライド間無音秒
--format wav|mp3         出力形式
--combine/--no-combine   結合音声の有無
--combined-name NAME     結合ファイル名
--include-slides SPEC    対象スライド
--wait-seconds S         Engine起動待ち上限
```

`--output-dir`、`--skip-empty`などを含む全アプリケーションオプションは、次で確認できます。

```bash
docker compose --profile tools run --rm pptx-narrator --help
```

#### 話速・抑揚・スライド間隔を調整する

```bash
make tts PPTX="sample/introduction_to_autosar.pptx" \
  STYLE_ID=888753760 \
  TTS_ARGS="--speed 0.95 --intonation 1.05 --slide-gap 1.0"
```

#### 一部のスライドだけを生成する

```bash
make tts PPTX="sample/introduction_to_autosar.pptx" \
  STYLE_ID=888753760 TTS_ARGS="--include-slides 1-5,8,10-12"
```

#### WAVで出力する

```bash
make tts PPTX="sample/introduction_to_autosar.pptx" \
  STYLE_ID=888753760 TTS_ARGS="--format wav"
```

#### 個別ファイルだけ生成する

```bash
make tts PPTX="sample/introduction_to_autosar.pptx" \
  STYLE_ID=888753760 TTS_ARGS="--no-combine"
```

### `make dict`

読み辞書を生成します。  
技術用語や社内用語の読みが記述された `dict/*.yaml` を AivisSpeech 互換 JSON へ変換し、  
Engineのユーザー辞書APIへ反映します。  
尚、`make tts` 実行時にYAML辞書ファイルが更新された場合は make ルールにて本処理が自動実行されます。  

```yaml
words:
  - surface: AUTOSAR
    pronunciation: オートザー
    replace: オートザー
    accent: 4
    priority: 8
    word_type: ORGANIZATION_NAME
```

`accent`、`priority`、`word_type` はAivisSpeech向けの拡張項目です。  
`surface` が重複すると、どのYAMLにあるかを表示して処理を停止します。  
辞書の詳細は [dict/README.md](dict/README.md) を参照してください。  
尚、生成物の `dict/aivis-user_dict.json` はGit管理しません。

### `make logs`

AivisSpeech Engineの動作ログを表示します。

### `make ps`

コンテナの稼働状況を表示します。

## トラブルシューティング

### 初回起動に時間がかかる

初回はBERT関連データの取得と初期化が必要です。`make voices`が完了するまで待機し、
時間がかかる場合は次でEngineのログを確認します。

```bash
make logs
```

### 話者が表示されない

モデルが`aivis-data/Models/`に配置されていることを確認し、追加後はEngineを再起動
します。

```bash
find aivis-data/Models -maxdepth 1 -type f -name '*.aivmx' -ls
make restart
make voices
```

### `aivis-data` への書き込みで失敗する

Engineの実行ユーザーに合わせて、データディレクトリの所有者を変更します。

```bash
sudo chown -R 1000:1000 aivis-data
```

## 注意事項

### 各種ライセンスについて

- AivisSpeech EngineはLGPL-3.0です。
- `python-pptx`、`requests`、PyYAML、FFmpegなどにも個別のライセンスがあります。
- `.aivmx`音声モデルはモデルごとにライセンス、利用条件、クレジット表記条件が異なります。
- 社内利用であっても、使用するモデルの規約を確認してください。
- このリポジトリには音声モデルを同梱しません。

「OSSのみ」という条件を厳密に適用する場合は、OSI承認ライセンスまたは
社内ルールで認められたライセンスのモデルだけを配置してください。
モデル配布ページの説明だけでなく、モデルに添付されたライセンス文書も保存してください。

## 付録

### 処理仕様

処理の流れは以下の通り。

1. `make tts`が読み辞書を生成し、AivisSpeech Engineへ反映する。
2. PowerPointファイルを読み込む。
3. 発表者ノートが既に存在するスライドだけを対象にする。
4. 空白行と行末空白を正規化する。
5. ノートを`output/<PowerPointファイル名(拡張子なし)>/notes`へ保存する。
6. `/audio_query`で読み上げクエリを作成する。このときEngineのユーザー辞書が適用される。
7. 話速、音高、抑揚、音量、前後無音を上書きする。
8. `/synthesis`でWAVを生成する。
9. 必要に応じてFFmpegでMP3へ変換する。
10. スライド間に無音を挿入し、一本の音声へ結合する。
11. 使用した話者と生成ファイルを`manifest.json`へ記録する。

### 運用上の注意

#### API公開範囲

ComposeではEngineのポートを次のようにバインドしています。

```yaml
127.0.0.1:10101:10101
```

社外・社内LANへAPIを公開する設計ではありません。複数ホストから利用する場合は、  
認証、TLS、アクセス制御、ログ管理を別途設計してください。

#### イメージの固定

`cpu-latest`は更新されます。検証済み環境を再現する場合は、  
運用開始時にイメージのタグまたはダイジェストを固定してください。

```bash
docker image inspect \
  ghcr.io/aivis-project/aivisspeech-engine:cpu-latest \
  --format '{{index .RepoDigests 0}}'
```

取得したダイジェストを`compose.yaml`の`image:`へ記録します。

#### GPU版エンジンの利用

GPU版へ切り替える場合の概略:

```yaml
aivis-engine:
  image: ghcr.io/aivis-project/aivisspeech-engine:nvidia-latest
  gpus: all
```

AivisSpeech Engineが利用するONNX Runtimeと、GPU実行環境のCUDA/cuDNN条件を満たす必要があります。  
まずCPU版で機能確認してから切り替えてください。

### 内部構成

Composeは、AivisSpeech Engineを提供する`aivis-engine`と、  
PowerPointファイル処理と音声生成を行う`pptx-narrator`の2サービスで構成されます。  
PythonとPythonパッケージは `pptx-narrator` コンテナ内だけに導入します。

`make setup`は`.env`へ現在のUID/GIDを記録し、`pptx-narrator`コンテナを同じUID/GIDで実行します。  
コンテナのHOMEはホストで管理する`.home/`であり、生成物とHOME内のファイルをホストユーザー所有にします。  
`aivis-engine`は公式イメージの既定ユーザーで実行します。

## 開発・保守向け情報

### エージェントへの引き継ぎ事項

次の順序で作業してください。

1. 使用許可された`.aivmx`モデルとライセンス文書を確定する。
2. `aivis-data/Models`へモデルを配置する。
3. Engineを起動し、`--list-voices`で`style_id`を記録する。
4. `--extract-only`で全ノートをレビューする。
5. 専門用語の読みを修正する。
6. 1～3枚だけ音声化し、話速・抑揚・読みを評価する。
7. 設定値を固定し、全スライドを生成する。
8. `manifest.json`、モデル名、モデルライセンス、Engineイメージの
   ダイジェストを成果物と一緒に保存する。
9. 必要ならGPU版へ移行する。
10. 社内配布前に音声を全編確認する。

以上。