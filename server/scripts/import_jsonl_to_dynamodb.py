from __future__ import annotations

import argparse
import json
import time
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeSerializer


DEFAULT_TABLE_NAME = "PokemonChampionsSpeedQuiz"
DEFAULT_REGION = "ap-northeast-2"
DEFAULT_SPECIES_FILE = Path(__file__).resolve().parents[1] / "data" / "curated" / "pokemon_species_regulation_m_b.jsonl"


def json_to_dynamodb_value(value: Any) -> Any:
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, list):
        return [json_to_dynamodb_value(item) for item in value]
    if isinstance(value, dict):
        return {key: json_to_dynamodb_value(item) for key, item in value.items()}
    return value


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


def create_table_if_missing(table_name: str, region_name: str, billing_mode: str) -> None:
    client = boto3.client("dynamodb", region_name=region_name)
    try:
        client.describe_table(TableName=table_name)
        print(f"table exists: {table_name}")
        return
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") != "ResourceNotFoundException":
            raise

    print(f"creating table: {table_name} ({region_name}, {billing_mode})")
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
        BillingMode=billing_mode,
    )

    while True:
        description = client.describe_table(TableName=table_name)["Table"]
        status = description["TableStatus"]
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


def preview_items(items: list[dict[str, Any]], limit: int = 3) -> None:
    serializer = TypeSerializer()
    print(f"items: {len(items)}")
    for item in items[:limit]:
        print(json.dumps({key: serializer.serialize(value) for key, value in item.items()}, ensure_ascii=False)[:1000])


def main() -> None:
    parser = argparse.ArgumentParser(description="Import reviewed JSONL records into a DynamoDB pk/sk table.")
    parser.add_argument("--table-name", default=DEFAULT_TABLE_NAME)
    parser.add_argument("--region", default=DEFAULT_REGION)
    parser.add_argument("--file", type=Path, default=DEFAULT_SPECIES_FILE)
    parser.add_argument("--create-table", action="store_true")
    parser.add_argument("--billing-mode", default="PAY_PER_REQUEST", choices=["PAY_PER_REQUEST", "PROVISIONED"])
    parser.add_argument("--dry-run", action="store_true", help="Validate and print the DynamoDB-shaped payload without writing.")
    args = parser.parse_args()

    items = load_jsonl(args.file)
    preview_items(items)
    if args.dry_run:
        print("dry-run only: no DynamoDB writes performed")
        return

    if args.create_table:
        create_table_if_missing(args.table_name, args.region, args.billing_mode)

    import_items(args.table_name, args.region, items)
    print(f"imported {len(items)} items into {args.table_name}")


if __name__ == "__main__":
    main()
