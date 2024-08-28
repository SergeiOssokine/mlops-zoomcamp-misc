import pulumi
import pulumi_aws as aws
from kinesis import Kinesis
from lambda_ import Lambda

config = pulumi.Config()
# AWS region to create resources
aws_region = config.get("awsRegion")
if aws_region is None:
    aws_region = "us-east-1"
# project_id
project_id = config.get("projectId")
if project_id is None:
    project_id = "mlops-zoomcamp"
source_stream_name = config.require("sourceStreamName")
output_stream_name = config.require("outputStreamName")
# s3_bucket
model_bucket = config.require("modelBucket")
# The Run ID for the model to use
run_id = config.require("runId")
lambda_function_name = config.require("lambdaFunctionName")
current_identity = aws.get_caller_identity_output()
account_id = current_identity.account_id

shard_level_metrics = config.get_object("shardLevelMetrics")

# ride_events
source_kinesis_stream = Kinesis(
    "sourceKinesisStream",
    {
        "retentionPeriod": 24,
        "shardCount": 1,
        "streamName": source_stream_name,
        "shardLevelMetrics": shard_level_metrics,
        "tags": project_id,
    },
)
# ride_predictions
output_kinesis_stream = Kinesis(
    "outputKinesisStream",
    {
        "retentionPeriod": 24,
        "shardCount": 1,
        "streamName": output_stream_name,
        "shardLevelMetrics": shard_level_metrics,
        "tags": project_id,
    },
)

output_stream_arn = output_kinesis_stream.stream_arn
source_stream_arn = source_kinesis_stream.stream_arn
lambda_function = Lambda(
    "lambdaFunction",
    {
        "imageUri": account_id.apply(
            lambda account_id: f"{account_id}.dkr.ecr.{aws_region}.amazonaws.com/duration-model:v0.5"
        ),
        "lambdaFunctionName": lambda_function_name,
        "modelBucket": model_bucket,
        "runId": run_id,
        "outputStreamName": output_stream_name,
        "outputStreamArn": output_stream_arn,
        "sourceStreamName": source_stream_name,
        "sourceStreamArn": source_stream_arn,
    },
)
pulumi.export("lambdaFunction", lambda_function_name)
pulumi.export("predictionsStreamName", output_stream_name)
