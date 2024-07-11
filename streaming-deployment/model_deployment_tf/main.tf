# Make sure to create state bucket beforehand
terraform {
  required_version = ">= 1.0"
  backend "s3" {
    bucket  = "tf-state-mlops-zoomcamp-988e46ce-82ea-4b22-97b2-e72b6d65b27e"
    key     = "mlops-zoomcamp-stg.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current_identity" {}

locals {
  account_id = data.aws_caller_identity.current_identity.account_id
}

# ride_events
module "source_kinesis_stream" {
  source           = "./modules/kinesis"
  retention_period = 24
  shard_count      = 1
  stream_name      = var.source_stream_name
  tags             = var.project_id
}

# ride_predictions
module "output_kinesis_stream" {
  source           = "./modules/kinesis"
  retention_period = 24
  shard_count      = 1
  stream_name      = var.output_stream_name
  tags             = var.project_id
}




module "lambda_function" {
  source               = "./modules/lambda"
  image_uri            = "${local.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/duration-model:v0.5"
  lambda_function_name = var.lambda_function_name
  model_bucket         = var.model_bucket
  run_id               = var.run_id
  output_stream_name   = var.output_stream_name
  output_stream_arn    = module.output_kinesis_stream.stream_arn
  source_stream_name   = var.source_stream_name
  source_stream_arn    = module.source_kinesis_stream.stream_arn
}

# For CI/CD
output "lambda_function" {
  value = var.lambda_function_name
}

output "predictions_stream_name" {
  value = var.output_stream_name
}
