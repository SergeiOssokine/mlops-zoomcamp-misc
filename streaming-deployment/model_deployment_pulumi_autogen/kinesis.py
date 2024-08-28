from typing import Optional, TypedDict

import pulumi
import pulumi_aws as aws
from pulumi import Input


class KinesisArgs(TypedDict, total=False):
    streamName: Input[str]
    shardCount: Input[float]
    retentionPeriod: Input[float]
    shardLevelMetrics: Input[list[str]]
    tags: Input[str]


class Kinesis(pulumi.ComponentResource):
    def __init__(
        self,
        name: str,
        args: KinesisArgs,
        opts: Optional[pulumi.ResourceOptions] = None,
    ):

        super().__init__("components:index:Kinesis", name, args, opts)

        # Create Kinesis Data Stream
        stream = aws.kinesis.Stream(
            f"{name}-stream",
            name=args["streamName"],
            shard_count=args["shardCount"],
            retention_period=args["retentionPeriod"],
            shard_level_metrics=args["shardLevelMetrics"],
            tags={
                "CreatedBy": args["tags"],
            },
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.stream_arn = stream.arn
        self.register_outputs({"streamArn": stream.arn})
