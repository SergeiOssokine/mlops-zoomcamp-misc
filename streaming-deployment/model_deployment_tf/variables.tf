variable "aws_region" {
  description = "AWS region to create resources"
  default     = "us-east-1"
  type        = string
}

variable "project_id" {
  description = "project_id"
  default     = "mlops-zoomcamp"
  type        = string
}

variable "source_stream_name" {
  description = ""
  type        = string
}

variable "output_stream_name" {
  description = ""
  type        = string

}

variable "model_bucket" {
  description = "s3_bucket"
  type        = string
}

variable "run_id" {
  description = "The Run ID for the model to use"
  type        = string
}


variable "lambda_function_name" {
  description = ""
  type        = string
}
