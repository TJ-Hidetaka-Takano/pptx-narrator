# 読み辞書

このディレクトリのYAMLファイルが読み辞書の正本です。現在は `make dict` が
AivisSpeech Engineのユーザー辞書へ変換・反映します。`replace` は将来ほかのTTSへ
切り替える際のテキスト置換用として保持します。

```yaml
words:
  - surface: AUTOSAR
    pronunciation: オートザー
    replace: オートザー
    accent: 4
    priority: 8
    word_type: ORGANIZATION_NAME
```

## 項目

| 項目 | 必須 | 説明 |
|---|---|---|
| `surface` | はい | 原文で辞書を適用する文字列 |
| `pronunciation` | はい | 読み。単語では全角カタカナ、複合語では表示・置換用の読み |
| `replace` | はい | 将来のTTS前処理で置換する文字列。現在のAivisSpeech連携では未使用 |
| `accent` | いいえ | 東京式アクセント型。`0`は平板型。省略時は`0` |
| `priority` | いいえ | 適用優先度。`0`～`10`、省略時は`5` |
| `word_type` | いいえ | AivisSpeechの品詞種別。省略時は`PROPER_NOUN` |
| `aivis_pronunciations` | 複合語のみ | アクセント句ごとに分けた全角カタカナの読み |
| `aivis_accents` | 複合語のみ | 各アクセント句のアクセント型 |

`surface`、`replace`、`pronunciation` は空でない文字列にします。同じ `surface` を
複数のYAMLに記載すると、生成時にエラーになります。

`word_type` に指定できる値は次のとおりです。

- `PROPER_NOUN`
- `LOCATION_NAME`
- `ORGANIZATION_NAME`
- `PERSON_NAME`
- `PERSON_FAMILY_NAME`
- `PERSON_GIVEN_NAME`
- `COMMON_NOUN`
- `VERB`
- `ADJECTIVE`
- `SUFFIX`

複合語は、AivisSpeech用に語ごとの読みとアクセントを指定できます。

```yaml
- surface: AUTOSAR AP
  pronunciation: オートザー エーピー
  replace: オートザー エーピー
  aivis_pronunciations: [オートザー, エーピー]
  aivis_accents: [0, 0]
```

`aivis_pronunciations` と `aivis_accents` は同じ要素数にします。読みは全角カタカナで
指定し、アクセント値は対応する読みのモーラ数以下にします。条件に合わない場合は、
Engineへ送信する前に生成処理を停止します。

## 生成と反映

`make dict` は `dict/aivis-user_dict.json` にAivisSpeech互換JSONを生成し、
`/import_user_dict?override=true` APIでEngineへ反映します。`word_type` に対応する品詞詳細と
文脈IDもAivisSpeechの定義に従って生成します。同じ `surface` は安定したUUIDで管理するため、
YAMLを更新して再実行すると既存の管理対象エントリを更新します。

YAMLから削除した語は、この生成ファイルで管理していたものに限りEngineから削除します。
Engineへの反映が失敗した場合は生成JSONを更新しないため、次回実行時に削除差分を再試行
できます。Engineへ手動で追加した語は変更しません。

```bash
make dict
```

生成JSONはGit管理しません。`make tts` は事前に `make dict` と同じ辞書反映処理を自動実行します。

Makeは次の依存関係を管理します。

- YAMLの編集・追加・削除時にJSONを再生成する
- `generate_dict.py`などアプリケーション変更時にDockerイメージを更新する
- 変換処理の変更時にJSONを再生成する
- YAMLに変更がなくても生成済みJSONをEngineへ再反映する

初回は `make setup` で環境を準備してください。その後は `make dict` または `make tts` で、
必要なイメージ更新・JSON生成・Engine反映が自動実行されます。
