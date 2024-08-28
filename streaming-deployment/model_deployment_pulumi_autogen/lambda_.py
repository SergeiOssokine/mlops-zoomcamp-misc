from typing import Any, Optional, TypedDict

import pulumi
import pulumi_aws as aws
from pulumi import Input


class LambdaArgs(TypedDict, total=False):
    sourceStreamName: Input[str]
    sourceStreamArn: Input[Any]
    outputStreamName: Input[Any]
    outputStreamArn: Input[Any]
    modelBucket: Input[Any]
    runId: Input[str]
    lambdaFunctionName: Input[Any]
    imageUri: Input[Any]


class Lambda(pulumi.ComponentResource):
    def __init__(
        self, name: str, args: LambdaArgs, opts: Optional[pulumi.ResourceOptions] = None
    ):
        super().__init__("components:index:Lambda", name, args, opts)

        iam_lambda = aws.iam.Role(
            f"{name}-iam_lambda",
            name=f"iam_{args['lambdaFunctionName']}",
            assume_role_policy="""{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": [
          "lambda.amazonaws.com",
          "kinesis.amazonaws.com"
          ]
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
""",
            opts=pulumi.ResourceOptions(parent=self),
        )

        allow_kinesis_processing = aws.iam.get_policy_output(
            arn="arn:aws:iam::aws:policy/service-role/AWSLambdaKinesisExecutionRole"
        )

        kinesis_processing = aws.iam.RolePolicyAttachment(
            f"{name}-kinesis_processing",
            role=iam_lambda.name,
            policy_arn=allow_kinesis_processing.arn,
            opts=pulumi.ResourceOptions(parent=self),
        )
        with open("lambda.log", "w") as fw:
            fw.write(str(args["outputStreamArn"]))
        # Allow write to output stream

        # Use apply to access the value of the Output
        def create_inline_policy(arn):
            return aws.iam.RolePolicy(
                f"{name}-inline_lambda_policy",
                name="LambdaInlinePolicy",
                role=iam_lambda.name,
                policy={
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": ["kinesis:PutRecords", "kinesis:PutRecord"],
                            "Resource": arn,
                        }
                    ],
                },
                opts=pulumi.ResourceOptions(parent=self, depends_on=[iam_lambda]),
            )

        inline_lambda_policy = args["outputStreamArn"].apply(create_inline_policy)

        # IAM for S3
        lambda_s3_role_policy = aws.iam.Policy(
            f"{name}-lambda_s3_role_policy",
            name=f"lambda_s3_policy_{args['lambdaFunctionName']}",
            description="IAM Policy for s3",
            policy={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "VisualEditor0",
                        "Effect": "Allow",
                        "Action": ["s3:Get*", "s3:List*"],
                        "Resource": [
                            f"arn:aws:s3:::{args['modelBucket']}",
                            f"arn:aws:s3:::{args['modelBucket']}/*",
                        ],
                    }
                ],
            },
            opts=pulumi.ResourceOptions(parent=self),
        )

        iam_policy_attach = aws.iam.RolePolicyAttachment(
            f"{name}-iam-policy-attach",
            role=iam_lambda.name,
            policy_arn=lambda_s3_role_policy.arn,
            opts=pulumi.ResourceOptions(parent=self),
        )

        kinesis_lambda = aws.lambda_.Function(
            f"{name}-kinesis_lambda",
            name=args["lambdaFunctionName"],
            image_uri=args["imageUri"],
            package_type="Image",
            role=iam_lambda.arn,
            tracing_config={
                "mode": "Active",
            },
            environment={
                "variables": {
                    "LOGGED_MODEL": f"s3://{args['modelBucket']}/1/{args['runId']}/artifacts/model",
                },
            },
            timeout=700,
            memory_size=512,
            opts=pulumi.ResourceOptions(parent=self),
        )

        # Lambda Invoke & Event Source Mapping:
        kinesis_lambda_event = aws.lambda_.FunctionEventInvokeConfig(
            f"{name}-kinesis_lambda_event",
            function_name=kinesis_lambda.name,
            maximum_event_age_in_seconds=60,
            maximum_retry_attempts=0,
            opts=pulumi.ResourceOptions(parent=self),
        )

        def create_event_source_mapping(arn):
            return aws.lambda_.EventSourceMapping(
                f"{name}-kinesis_mapping",
                event_source_arn=arn,
                function_name=kinesis_lambda.arn,
                starting_position="LATEST",
                opts=pulumi.ResourceOptions(parent=self),
            )

        lambda_source_mapping = args["sourceStreamArn"].apply(
            create_event_source_mapping
        )
