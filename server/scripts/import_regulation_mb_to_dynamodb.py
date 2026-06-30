from __future__ import annotations

import argparse
import json
import time
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import boto3
from botocore.exceptions import ClientError


DEFAULT_REGION = "ap-northeast-2"
CURATED = Path(__file__).resolve().parents[1] / "data" / "curated"

BATTLE_OPTIONS_FILE = CURATED / "pokemon_battle_options_regulation_m_b.json"
HELD_ITEMS_FILE = CURATED / "pokemon_held_items_regulation_m_b.jsonl"

MOVE_PK = "RULESET#pokemon_champions#REGULATION#M-B#MOVE"

BATTLE_OPTIONS_TABLE = "pokemon-battle-options"
HELD_ITEMS_TABLE = "pokemon-held-items"
MOVE_OPTIONS_TABLE = "pokemon-move-options"


def json_to_dynamodb_value(value: Any) -> Any:
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, list):
        return [json_to_dynamodb_value(item) for item in value]
    if isinstance(value, dict):
        return {key: json_to_dynamodb_value(item) for key, item in value.items()}
    return value


def require_keys(items: list[dict[str, Any]], label: str) -> None:
    for index, item in enumerate(items, start=1):
        if "pk" not in item or "sk" not in item:
            raise ValueError(f"{label}:{index} is missing pk/sk")


def load_json_list(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = list(raw.values()) if isinstance(raw, dict) else raw
    items = [json_to_dynamodb_value(item) for item in items]
    require_keys(items, str(path))
    return items


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            item = json.loads(line)
            if "pk" not in item or "sk" not in item:
                raise ValueError(f"{path}:{line_number} is missing pk/sk")
            items.append(json_to_dynamodb_value(item))
    return items


def derive_move_options(battle_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Dedupe availableMoves across all Pokémon by moveId into global move records.

    learnDetails is per-Pokémon, so it is dropped from the deduped global record.
    """
    moves: dict[str, dict[str, Any]] = {}
    for pokemon in battle_items:
        for move in pokemon.get("availableMoves", []) or []:
            move_id = move.get("moveId")
            if not move_id or move_id in moves:
                continue
            record = {key: val for key, val in move.items() if key != "learnDetails"}
            record["pk"] = MOVE_PK
            record["sk"] = f"MOVE#{move_id}"
            moves[move_id] = record
    return list(moves.values())


def create_table_if_missing(table_name: str, region_name: str) -> None:
    client = boto3.client("dynamodb", region_name=region_name)
    try:
        client.describe_table(TableName=table_name)
        print(f"table exists: {table_name}")
        return
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") != "ResourceNotFoundException":
            raise

    print(f"creating table: {table_name} ({region_name}, PAY_PER_REQUEST)")
    client.create_table(
        TableName=table_name,
        AttributeDefinitions=[
            {"AttributeName": "pk", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "pk", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    while True:
        status = client.describe_table(TableName=table_name)["Table"]["TableStatus"]
        if status == "ACTIVE":
            print(f"table active: {table_name}")
            return
        print(f"waiting for table to become ACTIVE: {status}")
        time.sleep(2)


def import_items(table_name: str, region_name: str, items: list[dict[str, Any]]) -> None:
    dynamodb = boto3.resource("dynamodb", region_name=region_name)
    table = cast(Any, dynamodb).Table(table_name)
    with table.batch_writer(overwrite_by_pkeys=["pk", "sk"]) as batch:
        for item in items:
            batch.put_item(Item=item)


def verify_query(table_name: str, region_name: str, pk: str, expected: int) -> None:
    from boto3.dynamodb.conditions import Key

    dynamodb = boto3.resource("dynamodb", region_name=region_name)
    table = cast(Any, dynamodb).Table(table_name)
    count = 0
    kwargs: dict[str, Any] = {"KeyConditionExpression": Key("pk").eq(pk), "Select": "COUNT"}
    while True:
        response = table.query(**kwargs)
        count += response["Count"]
        last = response.get("LastEvaluatedKey")
        if not last:
            break
        kwargs["ExclusiveStartKey"] = last
    status = "OK" if count == expected else "MISMATCH"
    print(f"  verify query {table_name} pk={pk}: {count} items (expected {expected}) [{status}]")


def verify_get(table_name: str, region_name: str, pk: str, sk: str) -> None:
    dynamodb = boto3.resource("dynamodb", region_name=region_name)
    table = cast(Any, dynamodb).Table(table_name)
    item = table.get_item(Key={"pk": pk, "sk": sk}).get("Item")
    print(f"  verify get_item {table_name} pk={pk} sk={sk}: {'found' if item else 'MISSING'}")


def preview(name: str, items: list[dict[str, Any]]) -> None:
    print(f"[{name}] items: {len(items)}")
    if items:
        sample = json.dumps(items[0], ensure_ascii=False, default=str)
        print(f"  sample: {sample[:400]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Regulation M-B data into 3 DynamoDB tables.")
    parser.add_argument("--region", default=DEFAULT_REGION)
    parser.add_argument("--dry-run", action="store_true", help="Validate and preview without writing.")
    args = parser.parse_args()

    battle = load_json_list(BATTLE_OPTIONS_FILE)
    held = load_jsonl(HELD_ITEMS_FILE)
    moves = derive_move_options(battle)

    specs = [
        (BATTLE_OPTIONS_TABLE, battle),
        (HELD_ITEMS_TABLE, held),
        (MOVE_OPTIONS_TABLE, moves),
    ]
    for name, items in specs:
        preview(name, items)

    if args.dry_run:
        print("dry-run only: no DynamoDB writes performed")
        return

    for table_name, items in specs:
        create_table_if_missing(table_name, args.region)
        import_items(table_name, args.region, items)
        print(f"imported {len(items)} items into {table_name}")

    print("verifying...")
    verify_query(BATTLE_OPTIONS_TABLE, args.region, battle[0]["pk"], len(battle))
    verify_query(MOVE_OPTIONS_TABLE, args.region, MOVE_PK, len(moves))
    verify_get(HELD_ITEMS_TABLE, args.region, held[0]["pk"], held[0]["sk"])


if __name__ == "__main__":
    main()
