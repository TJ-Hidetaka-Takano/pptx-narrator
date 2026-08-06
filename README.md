# PPTX Narrator

PowerPoint（`.pptx`）の**発表者ノート**を抽出し、ローカルの
AivisSpeech Engineでスライド単位の音声と結合音声を生成します。  
(OpenAI APIなどの外部TTSサービスは使用しません。)

## 1. 構成

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
|   `-- entrypoint
|-- GNUmakefile
|-- sample/
|   `-- introduction_to_autosar.pptx
|-- output/
|   `-- introduction_to_autosar/
|       |-- manifest.json
|       |-- narration.mp3
|       |-- notes/
|       `-- slides/
`-- README.md

```

`make setup`は`.env`へ現在のUID/GIDを記録し、`pptx-narrator`コンテナを同じ
UID/GIDで実行します。`pptx-narrator`コンテナのHOMEは、ホストで管理する`.home/`
です。これにより、生成物とコンテナ内HOMEのファイルがホストユーザー所有に
なります。`aivis-engine`は公式イメージの既定ユーザーで実行します。

Composeには次の2サービスがあります。

| サービス | 役割 |
|---|---|
| `aivis-engine` | AivisSpeech EngineのHTTP API。CPU版公式イメージを使用 |
| `pptx-narrator` | PPTXノート抽出、API呼び出し、FFmpegによる変換・結合 |

PythonとPythonパッケージは`pptx-narrator`コンテナ内だけに導入します。
Dockerfileでは仮想環境を作らず、`pip --break-system-packages`で
コンテナのシステムPythonへ直接導入します。

## 2. ライセンス上の注意

ソフトウェア本体と学習済み音声モデルのライセンスは別です。

- AivisSpeech EngineはLGPL-3.0です。
- `python-pptx`、`requests`、PyYAML、FFmpegなどにも個別のライセンスがあります。
- `.aivmx`音声モデルはモデルごとにライセンス、利用条件、クレジット表記条件が異なります。
- 社内利用であっても、使用するモデルの規約を確認してください。
- このリポジトリには音声モデルを同梱しません。

「OSSのみ」という条件を厳密に適用する場合は、OSI承認ライセンスまたは
社内ルールで認められたライセンスのモデルだけを配置してください。
モデル配布ページの説明だけでなく、モデルに添付されたライセンス文書も保存してください。

## 3. 必要環境

- Docker Engine
- Docker Compose v2
- CPU版では十分なメモリ
- 初回起動時にコンテナイメージやBERT関連データを取得するためのネットワーク接続
- 合成処理そのものは、必要データを取得済みならローカルで実行可能

NVIDIA GPU版へ変更する場合は、ホスト側にNVIDIA Container Toolkitが必要です。
本構成はセットアップを単純にするためCPU版を標準としています。

## 4. 初期準備

### 4.1 Makeコマンドの概要

以降のDocker Compose操作は、リポジトリ直下で`make`から実行できます。

```bash
make setup
make launch
make tts PPTX="sample/introduction_to_autosar.pptx"
make shutdown
```

入力PPTXはこのリポジトリ配下に置きます。`make tts`は指定したPPTXを直接処理し、
結合音声を`output/<PPTXファイル名（拡張子なし）>/narration.mp3`へ生成します。
例えば上記の入力なら`output/introduction_to_autosar/narration.mp3`です。

追加で用意しているコマンド:

```bash
make voices                         # 利用可能な話者・style_idを表示
make extract PPTX="sample/introduction_to_autosar.pptx" # 発表者ノートだけを抽出
make dict                           # 読み辞書を生成し、Engineへ反映
make logs                           # Engineログを追跡
make ps                             # コンテナ状態を表示
make restart                        # モデル追加後などにEngineを再起動
```

`STYLE_ID`と、アプリケーションの追加オプションは次のように指定できます。

```bash
make tts PPTX="sample/introduction_to_autosar.pptx" STYLE_ID=888753760 \
  TTS_ARGS="--speed 0.95 --intonation 1.05 --slide-gap 1.0"
```

全コマンドは`make help`で確認できます。

### 4.2 ディレクトリを作成する

リポジトリのルートで実行します。

```bash
mkdir -p output aivis-data/Models
```

`aivis-engine`は公式イメージの既定一般ユーザー（通常UID 1000）で実行されます。
書き込み権限でエラーになる場合は、Engine用のデータディレクトリだけをそのUIDに
合わせます。

```bash
sudo chown -R 1000:1000 aivis-data
```

### 4.3 音声モデルを配置する

ライセンスを確認したAivisSpeech形式のモデルファイル（`.aivmx`）を配置します。

```text
aivis-data/Models/<model-name>.aivmx
```

モデルのライセンス文書も、別途社内で追跡できる場所へ保管してください。

### 4.4 サンプルPPTX

リポジトリには、発表者ノートを含むAUTOSAR入門のサンプルを同梱しています。
処理対象のPPTXは、このリポジトリ配下に配置して`PPTX`へ相対パスを指定します。

```bash
make tts PPTX="sample/introduction_to_autosar.pptx"
```

## 5. ビルドと起動

```bash
make setup
make launch
```

EngineのSwagger UIはホストから次で確認できます。

```text
http://127.0.0.1:10101/docs
```

ポートは`127.0.0.1`だけに公開しているため、標準状態では外部ホストから
直接アクセスできません。

## 6. 音声モデルを確認する

モデル配置後、話者名、スタイル名、`style_id`を確認します。

```bash
make voices
```

出力例:

```text
style_id=888753760    speaker=話者名    style=ノーマル
```

利用可能なモデルが表示されない場合は、次を確認します。

```bash
make logs
find aivis-data/Models -maxdepth 1 -type f -name '*.aivmx' -ls
```

モデル追加後に認識されない場合はEngineを再起動します。

```bash
make restart
```

## 7. 発表者ノートだけを抽出する

TTSの前に、抽出結果をレビューすることを推奨します。

```bash
make extract PPTX="sample/introduction_to_autosar.pptx"
```

抽出結果:

```text
output/introduction_to_autosar/notes/slide-001.txt
output/introduction_to_autosar/notes/slide-002.txt
...
```

`python-pptx`の`has_notes_slide`で既存ノートの有無を確認し、
`notes_text_frame`から本文を取得します。ノートのないスライドを
処理のためだけに新規作成しない実装です。

## 8. 音声を生成する

### 8.1 最初に見つかったスタイルを使用する

```bash
make tts PPTX="sample/introduction_to_autosar.pptx"
```

標準では次を生成します。

```text
output/
└── <PPTXファイル名（拡張子なし）>/
    ├── notes/
    ├── slides/
    │   ├── slide-001.mp3
    │   ├── slide-002.mp3
    │   └── ...
    ├── manifest.json
    └── narration.mp3
```

### 8.2 スタイルIDを明示する

再現性のため、実運用では`--style-id`の指定を推奨します。

```bash
make tts PPTX="sample/introduction_to_autosar.pptx" \
  STYLE_ID=888753760
```

### 8.3 話速・抑揚・スライド間隔を調整する

```bash
make tts PPTX="sample/introduction_to_autosar.pptx" \
  STYLE_ID=888753760 \
  TTS_ARGS="--speed 0.95 --intonation 1.05 --slide-gap 1.0"
```

### 8.4 一部のスライドだけを生成する

```bash
make tts PPTX="sample/introduction_to_autosar.pptx" \
  STYLE_ID=888753760 TTS_ARGS="--include-slides 1-5,8,10-12"
```

### 8.5 WAVで出力する

```bash
make tts PPTX="sample/introduction_to_autosar.pptx" \
  STYLE_ID=888753760 TTS_ARGS="--format wav"
```

### 8.6 個別ファイルだけ生成する

```bash
make tts PPTX="sample/introduction_to_autosar.pptx" \
  STYLE_ID=888753760 TTS_ARGS="--no-combine"
```

### 8.7 読み辞書

`dict/*.yaml`で、技術用語や社内用語の読みを管理します。`make dict` はYAMLを
AivisSpeech互換JSONへ変換し、Engineのユーザー辞書APIへ反映します。`make tts` は
この処理を事前に自動実行するため、原文の発表者ノートをそのままEngineへ渡しても
ユーザー辞書が適用されます。

```yaml
words:
  - surface: AUTOSAR
    pronunciation: オートザー
    replace: オートザー
    accent: 4
    priority: 8
    word_type: ORGANIZATION_NAME
```

`accent`、`priority`、`word_type` はAivisSpeech向けの拡張項目です。`surface` が
重複すると、どのYAMLにあるかを表示して処理を停止します。辞書を単独で更新するには
次を実行します。

```bash
make dict
```

生成物の `dict/aivis-user_dict.json` はGit管理しません。辞書の詳細は
[dict/README.md](dict/README.md) を参照してください。

MakeはYAMLと変換スクリプトの更新を検知し、必要に応じてDockerイメージとJSONを
再生成します。YAMLに変更がない場合も、生成済みJSONをEngineへ再反映します。

## 9. 主なオプション

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

全オプション:

```bash
make help
```

## 10. 処理仕様

1. `make tts`が読み辞書を生成し、AivisSpeech Engineへ反映する。
2. PPTXを読み込む。
3. 発表者ノートが既に存在するスライドだけを対象にする。
4. 空白行と行末空白を正規化する。
5. ノートを`output/<PPTX名>/notes`へ保存する。
6. `/audio_query`で読み上げクエリを作成する。このときEngineのユーザー辞書が適用される。
7. 話速、音高、抑揚、音量、前後無音を上書きする。
8. `/synthesis`でWAVを生成する。
9. 必要に応じてFFmpegでMP3へ変換する。
10. スライド間に無音を挿入し、一本の音声へ結合する。
11. 使用した話者と生成ファイルを`manifest.json`へ記録する。

## 11. 運用上の注意

### 原稿レビュー

TTSへ渡す前に`--extract-only`で次を確認してください。

- 英字略語の読み
- `AUTOSAR AP`、`ARA`、`SOA`、`SOME/IP`などの専門用語
- 記号、括弧、スラッシュ
- 箇条書きの読み順
- 読み上げ不要なノート

読み方を安定させるには、発表者ノート側を読み上げ用表記へ直す方法が確実です。

### API公開範囲

ComposeではEngineのポートを次のようにバインドしています。

```yaml
127.0.0.1:10101:10101
```

社外・社内LANへAPIを公開する設計ではありません。複数ホストから利用する場合は、
認証、TLS、アクセス制御、ログ管理を別途設計してください。

### イメージの固定

`cpu-latest`は更新されます。検証済み環境を再現する場合は、
運用開始時にイメージのタグまたはダイジェストを固定してください。

```bash
docker image inspect \
  ghcr.io/aivis-project/aivisspeech-engine:cpu-latest \
  --format '{{index .RepoDigests 0}}'
```

取得したダイジェストを`compose.yaml`の`image:`へ記録します。

### GPU版

GPU版へ切り替える場合の概略:

```yaml
aivis-engine:
  image: ghcr.io/aivis-project/aivisspeech-engine:nvidia-latest
  gpus: all
```

AivisSpeech Engineが利用するONNX Runtimeと、GPU実行環境のCUDA/cuDNN条件を
満たす必要があります。まずCPU版で機能確認してから切り替えてください。

## 12. 停止

```bash
make shutdown
```

`aivis-data`はホストのバインドマウントなので、`down`後もモデルとキャッシュは残ります。

## 13. エージェントへの引き継ぎ事項

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

## 14. 既知の制約

- ノート内の書式、強調、アニメーション、タイミング情報は使用しません。
- 発表者ノートを単純なテキストとして読みます。
- PowerPointのスライド表示時間とは同期しません。
- 音声モデル自体は同梱しません。
- 読み間違いは、`dict/*.yaml`の読み辞書または原稿表記で調整します。
- `cpu-latest`を使うため、将来のEngine更新でAPI差分が発生する可能性があります。
