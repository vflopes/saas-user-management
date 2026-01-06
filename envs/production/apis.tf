module "apis" {
  source = "./apis"

  lambda_logging_arn = data.aws_iam_policy.lambda_logging.arn
  api_gateway_id     = data.aws_ssm_parameter.api_gateway_id.value

}
