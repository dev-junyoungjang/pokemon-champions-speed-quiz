from __future__ import annotations

import argparse
import time

import boto3
from botocore.exceptions import ClientError

DEFAULT_TABLE_NAME = "user-pokemon-data"
DEFAULT_REGION = "ap-northeast-2"


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the DynamoDB table for user Pokémon/team data.")
    parser.add_argument("--table-name", default=DEFAULT_TABLE_NAME)
    parser.add_argument("--region", default=DEFAULT_REGION)
    parser.add_argument("--billing-mode", default="PAY_PER_REQUEST", choices=["PAY_PER_REQUEST", "PROVISIONED"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print(f"table-name: {args.table_name}")
    print("key-schema: pk HASH, sk RANGE")
    if args.dry_run:
        print("dry-run only: no DynamoDB table created")
        return
    create_table_if_missing(args.table_name, args.region, args.billing_mode)


if __name__ == "__main__":
    main()
