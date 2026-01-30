import boto3

__all__ = ["list_regions"]


def list_regions(service_name: str = "ec2") -> list[str]:
    return boto3._get_default_session().get_available_regions(service_name)
