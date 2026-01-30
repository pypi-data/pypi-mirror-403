from contextlib import contextmanager
from typing import Iterator, cast

import boto3
import botocore.client
from botocore.config import Config

__all__ = ["Client"]


@contextmanager
def Client(
    aws_service: str, region: str
) -> Iterator[botocore.client.BaseClient]:
    cfg = Config(region_name=region)
    c = cast(botocore.client.BaseClient, boto3.client(aws_service, config=cfg))

    try:
        yield c
    finally:
        c.close()
