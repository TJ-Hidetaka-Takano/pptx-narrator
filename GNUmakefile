DEPS		= .env
COMPOSE		:= docker compose
PPTX		?=
PPTX_FILE	:= $(notdir $(PPTX))
PPTX_NAME	:= $(basename $(PPTX_FILE))
STYLE_ID	?=
TTS_ARGS	?=

.PHONY: help
.DEFAULT_GOAL = help

#--------------------------------------------------------------------------------------------------
# 環境構築
#--------------------------------------------------------------------------------------------------
.PHONY: setup
# pptx-narratorイメージの構築と、ホスト側データディレクトリの作成
setup: $(DEPS)
	@mkdir -p .home output aivis-data/Models
	@echo '[make] setup: build docker images for pptx-narrator'
	$(COMPOSE) build --no-cache pptx-narrator

#--------------------------------------------------------------------------------------------------
# AivisSpeech Engine サービスの起動・停止
#--------------------------------------------------------------------------------------------------
.PHONY: launch shutdown restart
# Engine サービスの起動
launch: $(DEPS)
	@mkdir -p .home aivis-data/Models
	@echo '[make] launch: AivisSpeech Engine service'
	$(COMPOSE) up -d aivis-engine

# Engine サービスの停止・削除
shutdown: $(DEPS)
	@echo '[make] shutdown: AivisSpeech Engine service'
	$(COMPOSE) down

# Engineの再起動
restart: $(DEPS)
	@echo '[make] restart: AivisSpeech Engineを再起動します'
	$(COMPOSE) restart aivis-engine

#--------------------------------------------------------------------------------------------------
# ナレーション音声の生成
#--------------------------------------------------------------------------------------------------
.PHONY: tts extract voices check-pptx
# PPTX指定の検証（pptx-narrator配下のファイルのみ受け付ける）
check-pptx:
	@test -n "$(PPTX)" || { echo '[ERROR] PPTXを指定してください。例: make tts PPTX=/path/to/slides.pptx' >&2; exit 2; }
	@test -f "$(PPTX)" || { echo "[ERROR] PPTXファイルが見つかりません: $(PPTX)" >&2; exit 2; }
	@case "$(PPTX_FILE)" in *.pptx|*.PPTX) ;; *) echo "[ERROR] .pptxファイルを指定してください: $(PPTX)" >&2; exit 2;; esac
	@project_path="$$(pwd -P)"; \
	pptx_path="$$(cd "$$(dirname "$(PPTX)")" && pwd -P)/$$(basename "$(PPTX)")"; \
	case "$$pptx_path" in "$$project_path"/*) ;; *) \
		echo "[ERROR] pptx-narrator配下のPPTXを指定してください: $(PPTX)" >&2; exit 2;; \
	esac

# PPTXの発表者ノートから結合音声を生成
tts: $(DEPS) check-pptx launch
	@mkdir -p "output/$(PPTX_NAME)"
	@echo "[make] tts: output/$(PPTX_NAME)/narration.mp3 を生成します"
	$(COMPOSE) --profile tools run --rm pptx-narrator \
		"$(PPTX)" \
		$(if $(STYLE_ID),--style-id $(STYLE_ID)) $(TTS_ARGS) \
		--output-dir "output/$(PPTX_NAME)" \
		--combined-name narration

# PPTXから発表者ノートだけを抽出
extract: $(DEPS) check-pptx
	@mkdir -p "output/$(PPTX_NAME)"
	@echo "[make] extract: $(PPTX_FILE) から発表者ノートを抽出します"
	$(COMPOSE) --profile tools run --rm pptx-narrator \
		"$(PPTX)" --output-dir "output/$(PPTX_NAME)" --extract-only $(TTS_ARGS)

# 利用可能な話者・スタイルを表示
voices: $(DEPS) launch
	@echo '[make] voices: 利用可能な話者・style_idを表示します'
	$(COMPOSE) --profile tools run --rm pptx-narrator --list-voices

#--------------------------------------------------------------------------------------------------
# その他ユーティリティ
#--------------------------------------------------------------------------------------------------
.PHONY: logs ps pre-commit
# Engineログの追跡
logs: $(DEPS)
	$(COMPOSE) logs -f aivis-engine

# コンテナ状態の表示
ps: $(DEPS)
	$(COMPOSE) ps

#--------------------------------------------------------------------------------------------------
# ヘルプ
#--------------------------------------------------------------------------------------------------
help:
	@printf '%s\n' \
	  '使い方:' \
	  '  make setup                                     # コンテナ環境を構築する' \
	  '  make launch                                    # AivisSpeech Engineを起動する' \
	  '  make tts PPTX=sample/introduction_to_autosar.pptx # ナレーション音声を生成する' \
	  '  make shutdown                                  # コンテナを停止・削除する' \
	  '' \
	  '音声生成の指定例:' \
	  '  make tts PPTX=sample/introduction_to_autosar.pptx STYLE_ID=888753760' \
	  '  make tts PPTX=sample/introduction_to_autosar.pptx TTS_ARGS="--speed 0.95 --slide-gap 1.0"' \
	  '' \
	  'その他のコマンド:' \
	  '  make voices                                    # 利用可能な話者・style_idを表示する' \
	  '  make extract PPTX=sample/introduction_to_autosar.pptx # 発表者ノートだけを抽出する' \
	  '  make restart                                   # AivisSpeech Engineを再起動する' \
	  '  make logs                                      # AivisSpeech Engineのログを追跡する' \
	  '  make ps                                        # コンテナの状態を表示する' \
	  '' \
	  '  make help                                      # このヘルプの表示'

# Compose用の実行ユーザー情報
.env: GNUmakefile
	@echo "UID=$(shell id -u)" > $@
	@echo "GID=$(shell id -g)" >> $@
