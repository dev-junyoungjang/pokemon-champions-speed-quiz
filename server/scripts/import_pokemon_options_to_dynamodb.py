from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import boto3


DEFAULT_TABLE_NAME = "pokemon-options"
DEFAULT_REGION = "ap-northeast-2"
DEFAULT_OPTIONS_FILE = Path(__file__).resolve().parents[1] / "data" / "curated" / "pokemon_battle_options_regulation_m_b.json"


def json_to_dynamodb_value(value: Any) -> Any:
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, list):
        return [json_to_dynamodb_value(item) for item in value]
    if isinstance(value, dict):
        return {key: json_to_dynamodb_value(item) for key, item in value.items()}
    return value


def load_options(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        items = list(raw.values())
    else:
        items = raw
    normalized = [json_to_dynamodb_value(item) for item in items]
    for index, item in enumerate(normalized, start=1):
        if "pk" not in item or "sk" not in item:
            raise ValueError(f"{path}:{index} is missing pk/sk")
    return normalized


def import_items(table_name: str, region_name: str, items: list[dict[str, Any]]) -> None:
    dynamodb = boto3.resource("dynamodb", region_name=region_name)
    table = cast(Any, dynamodb).Table(table_name)
    with table.batch_writer(overwrite_by_pkeys=["pk", "sk"]) as batch:
        for item in items:
            batch.put_item(Item=item)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Pokémon ability/move option records into DynamoDB.")
    parser.add_argument("--table-name", default=DEFAULT_TABLE_NAME)
    parser.add_argument("--region", default=DEFAULT_REGION)
    parser.add_argument("--file", type=Path, default=DEFAULT_OPTIONS_FILE)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    items = load_options(args.file)
    print(f"items: {len(items)}")
    print(json.dumps(items[0], ensure_ascii=False)[:1000] if items else "no items")
    if args.dry_run:
        print("dry-run only: no DynamoDB writes performed")
        return

    import_items(args.table_name, args.region, items)
    print(f"imported {len(items)} items into {args.table_name}")


if __name__ == "__main__":
    main()
