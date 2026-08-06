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

`surface`、`replace`、`pronunciation` は空でない文字列で指定してください。
`accent` は東京式アクセント型（省略時 `0`）、`priority` は0～10（省略時 `5`）です。
`word_type` はAivisSpeechの品詞種別で、省略時は `PROPER_NOUN` です。使える値は
`PROPER_NOUN`、`ORGANIZATION_NAME`、`PERSON_NAME`、`LOCATION_NAME`、`COMMON_NOUN`
などです。同じ `surface` を複数のYAMLに記載すると、生成時にエラーになります。

複合語は、AivisSpeech用に語ごとの読みとアクセントを指定できます。

```yaml
- surface: AUTOSAR AP
  pronunciation: オートザー エーピー
  replace: オートザー エーピー
  aivis_pronunciations: [オートザー, エーピー]
  aivis_accents: [0, 0]
```

`aivis_pronunciations` と `aivis_accents` は同じ要素数にします。

`make dict` は `dict/aivis-user_dict.json` にAivisSpeech互換JSONを生成し、
`/import_user_dict?override=true` APIでEngineへ反映します。同じ `surface` は安定したUUIDで
管理するため、YAMLを更新して再実行すると既存の管理対象エントリを更新します。YAMLから
削除した語も、この生成ファイルで管理していたものに限りEngineから削除します。Engineへ
手動で追加した語は変更しません。

```bash
make dict
```

生成JSONはGit管理しません。`make tts` は事前に `make dict` と同じ辞書反映処理を自動実行します。
YAMLの編集・追加・削除、または変換スクリプトの変更時は、Makeの依存関係によってJSONも
再生成されます。Engine再起動後も `make dict`（または `make tts`）で生成済みJSONを再反映します。
