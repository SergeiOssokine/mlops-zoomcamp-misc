resource "aws_lambda_function" "kinesis_lambda" {
  function_name = var.lambda_function_name
  # This can also be any base image to bootstrap the lambda config, unrelated to your Inference service on ECR
  # which would be anyway updated regularly via a CI/CD pipeline
  image_uri    = var.image_uri # required-argument
  package_type = "Image"
  role         = aws_iam_role.iam_lambda.arn
  tracing_config {
    mode = "Active"
  }
  // This step is optional (environment)
  environment {
    variables = {
      LOGGED_MODEL = "s3://${var.model_bucket}/1/${var.run_id}/artifacts/model"
    }
  }
  timeout     = 700
  memory_size = 512
}

# Lambda Invoke & Event Source Mapping:

resource "aws_lambda_function_event_invoke_config" "kinesis_lambda_event" {
  function_name                = aws_lambda_function.kinesis_lambda.function_name
  maximum_event_age_in_seconds = 60
  maximum_retry_attempts       = 0
}

resource "aws_lambda_event_source_mapping" "kinesis_mapping" {
  event_source_arn  = var.source_stream_arn
  function_name     = aws_lambda_function.kinesis_lambda.arn
  starting_position = "LATEST"

}
