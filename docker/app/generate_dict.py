#!/usr/bin/env python3
"""YAMLで管理する読み辞書を、TTS前処理用のJSONへ変換する。"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

import requests
import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="dict/*.yaml を読み、読み置換用JSON辞書を生成します。"
    )
    parser.add_argument(
        "--dict-dir", type=Path, default=Path("dict"), help="YAML辞書のディレクトリ"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dict/aivis-user_dict.json"),
        help="AivisSpeech互換ユーザー辞書JSONの出力先",
    )
    parser.add_argument(
        "--engine-url",
        default=os.getenv("AIVIS_ENGINE_URL", "http://aivis-engine:10101"),
        help="AivisSpeech EngineのURL",
    )
    apply_group = parser.add_mutually_exclusive_group()
    apply_group.add_argument(
        "--apply", action="store_true", help="生成した辞書をEngine APIへインポートする"
    )
    apply_group.add_argument(
        "--apply-existing",
        action="store_true",
        help="既に生成済みのJSONをEngine APIへインポートする",
    )
    return parser.parse_args()


def validate_word(word: Any, source: Path, index: int) -> dict[str, Any]:
    if not isinstance(word, dict):
        raise ValueError(f"{source}:{index}: words の各要素はマッピングにしてください")

    surface = word.get("surface")
    replacement = word.get("replace")
    pronunciation = word.get("pronunciation")
    for field, value in (
        ("surface", surface),
        ("replace", replacement),
        ("pronunciation", pronunciation),
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{source}:{index}: {field} は空でない文字列にしてください")
    for field, default, minimum, maximum in (
        ("accent", 0, 0, None),
        ("priority", 5, 0, 10),
    ):
        value = word.get(field, default)
        if not isinstance(value, int) or isinstance(value, bool) or value < minimum or (
            maximum is not None and value > maximum
        ):
            range_text = f"{minimum}～{maximum}" if maximum is not None else f"{minimum}以上"
            raise ValueError(f"{source}:{index}: {field} は {range_text} の整数にしてください")
    word_type = word.get("word_type", "PROPER_NOUN")
    allowed_word_types = {
        "PROPER_NOUN", "LOCATION_NAME", "ORGANIZATION_NAME", "PERSON_NAME",
        "PERSON_FAMILY_NAME", "PERSON_GIVEN_NAME", "COMMON_NOUN", "VERB",
        "ADJECTIVE", "SUFFIX",
    }
    if word_type not in allowed_word_types:
        raise ValueError(f"{source}:{index}: word_type が不正です: {word_type!r}")
    aivis_pronunciations = word.get("aivis_pronunciations", [pronunciation])
    aivis_accents = word.get("aivis_accents", [word.get("accent", 0)])
    if not isinstance(aivis_pronunciations, list) or not aivis_pronunciations or not all(
        isinstance(value, str) and value.strip() for value in aivis_pronunciations
    ):
        raise ValueError(f"{source}:{index}: aivis_pronunciations は空でない文字列のリストにしてください")
    if not isinstance(aivis_accents, list) or len(aivis_accents) != len(aivis_pronunciations) or not all(
        isinstance(value, int) and not isinstance(value, bool) and value >= 0
        for value in aivis_accents
    ):
        raise ValueError(
            f"{source}:{index}: aivis_accents は読みと同数の0以上の整数リストにしてください"
        )
    return word


def make_aivis_word(word: dict[str, Any]) -> dict[str, Any]:
    """AivisSpeech Engineの/import_user_dict互換形式へ変換する。"""
    surface = word["surface"]
    pronunciations = word.get("aivis_pronunciations", [word["pronunciation"]])
    accents = word.get("aivis_accents", [word.get("accent", 0)])
    return {
        "surface": surface,
        "priority": word.get("priority", 5),
        "part_of_speech": "名詞",
        "part_of_speech_detail_1": "固有名詞",
        "part_of_speech_detail_2": "一般",
        "part_of_speech_detail_3": "*",
        "word_type": word.get("word_type", "PROPER_NOUN"),
        "inflectional_type": "*",
        "inflectional_form": "*",
        "stem": [surface],
        "yomi": pronunciations,
        "pronunciation": pronunciations,
        "accent_type": accents,
        "mora_count": [],
        "accent_associative_rule": "*",
    }


def load_dictionary(dict_dir: Path) -> dict[str, dict[str, Any]]:
    if not dict_dir.is_dir():
        raise ValueError(f"辞書ディレクトリが存在しません: {dict_dir}")

    dictionary: dict[str, dict[str, Any]] = {}
    sources: dict[str, Path] = {}
    yaml_files = sorted((*dict_dir.glob("*.yaml"), *dict_dir.glob("*.yml")))
    for yaml_path in yaml_files:
        with yaml_path.open(encoding="utf-8") as file:
            data = yaml.safe_load(file)
        if data is None:
            continue
        if not isinstance(data, dict) or not isinstance(data.get("words"), list):
            raise ValueError(f"{yaml_path}: words のリストが必要です")

        for index, word in enumerate(data["words"], start=1):
            word = validate_word(word, yaml_path, index)
            surface = word["surface"]
            if surface in dictionary:
                raise ValueError(
                    f"重複した surface: {surface!r} "
                    f"({sources[surface]} と {yaml_path})"
                )
            dictionary[surface] = make_aivis_word(word)
            sources[surface] = yaml_path

    # UUIDを安定化し、同じsurfaceを再インポートしたときはEngine側の既存語を更新する。
    return {
        str(uuid.uuid5(uuid.NAMESPACE_URL, f"pptx-narrator:{surface}")): entry
        for surface, entry in sorted(dictionary.items(), key=lambda item: item[0])
    }


def write_dictionary(dictionary: dict[str, dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(dictionary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def read_previous_dictionary(output_path: Path) -> dict[str, Any]:
    if not output_path.is_file():
        return {}
    data = json.loads(output_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not all(isinstance(key, str) for key in data):
        raise ValueError(f"既存の生成辞書の形式が不正です: {output_path}")
    return data


def apply_dictionary(
    dictionary: dict[str, dict[str, Any]], previous_dictionary: dict[str, Any], engine_url: str
) -> None:
    response = requests.post(
        f"{engine_url.rstrip('/')}/import_user_dict",
        params={"override": "true"},
        json=dictionary,
        timeout=30,
    )
    response.raise_for_status()
    # 専用の生成ファイルに記録されたUUIDだけを削除するため、手動登録した語は消さない。
    for word_uuid in previous_dictionary.keys() - dictionary.keys():
        response = requests.delete(
            f"{engine_url.rstrip('/')}/user_dict_word/{word_uuid}", timeout=30
        )
        response.raise_for_status()


def main() -> int:
    args = parse_args()
    if args.apply_existing:
        dictionary = read_previous_dictionary(args.output)
        if not dictionary:
            raise ValueError(f"生成済みのユーザー辞書がありません: {args.output}")
        apply_dictionary(dictionary, {}, args.engine_url)
        print(f"AivisSpeech Engineへユーザー辞書を反映しました: {args.engine_url}")
        return 0

    dictionary = load_dictionary(args.dict_dir)
    previous_dictionary = read_previous_dictionary(args.output)
    write_dictionary(dictionary, args.output)
    print(f"読み辞書を生成しました: {args.output} ({len(dictionary)} 語)")
    if args.apply:
        apply_dictionary(dictionary, previous_dictionary, args.engine_url)
        print(f"AivisSpeech Engineへユーザー辞書を反映しました: {args.engine_url}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, requests.RequestException, yaml.YAMLError) as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        raise SystemExit(1)
