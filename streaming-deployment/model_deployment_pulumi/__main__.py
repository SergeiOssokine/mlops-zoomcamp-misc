"""Reproduce a simple streaming model using Pulumi"""

import pulumi
import pulumi_aws_native as aws_native

config = pulumi.Config()
input_stream_name = config.require("input_stream_name")
output_stream_name = config.require("output_stream_name")
image_uri = config.require("image_uri")
model_bucket = config.require("model_bucket")
run_id = config.require("run_id")

# Create the input Kinesis stream
input_stream = aws_native.kinesis.Stream(
    input_stream_name, name=input_stream_name, shard_count=1
)

# Create the output Kinesis stream
output_stream = aws_native.kinesis.Stream(
    output_stream_name, name=output_stream_name, shard_count=1
)


# Create the IAM role
iam_role = aws_native.iam.Role(
    "LambdaKinesisIAMRole",
    assume_role_policy_document={
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": ["lambda.amazonaws.com", "kinesis.amazonaws.com"],
                },
                "Action": "sts:AssumeRole",
            }
        ],
    },
    role_name="LambdaKinesisIAMRole",
    managed_policy_arns=[
        "arn:aws:iam::aws:policy/service-role/AWSLambdaKinesisExecutionRole"
    ],
    policies=[
        {
            "policy_name": "KinesisOutput",
            "policy_document": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": ["kinesis:PutRecords", "kinesis:PutRecord"],
                        "Resource": output_stream.arn,
                    }
                ],
            },
        },
        {
            "policy_name": "LambdaS3Access",
            "policy_document": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "VisualEditor0",
                        "Effect": "Allow",
                        "Action": ["s3:Get*", "s3:List*"],
                        "Resource": [
                            f"arn:aws:s3:::{model_bucket}",
                            f"arn:aws:s3:::{model_bucket}/*",
                        ],
                    }
                ],
            },
        },
    ],
)

# Create the lambda function
lambda_func = aws_native.lambda_.Function(
    "predict",
    memory_size=512,
    timeout=700,
    package_type="Image",
    code={"image_uri": image_uri},
    role=iam_role.arn,
    environment={
        "variables": {"LOGGED_MODEL": f"s3://{model_bucket}/1/{run_id}/artifacts/model"}
    },
)
# Add the trigger from Kinesis
ev_source_mapping = aws_native.lambda_.EventSourceMapping(
    "output_mapping",
    function_name=lambda_func.arn,
    event_source_arn=input_stream.arn,
    starting_position="LATEST",
)


# Export the ARNs of the streams
pulumi.export("input_stream_arn", input_stream.arn)
pulumi.export("output_stream_arn", output_stream.arn)
