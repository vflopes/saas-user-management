locals {
  // https://docs.aws.amazon.com/systems-manager/latest/userguide/ps-integration-lambda-extensions.html#ps-integration-lambda-extensions-add

  parameters_and_secrets_layer_arns = {
    "us-east-1" = "arn:aws:lambda:us-east-1:177933569100:layer:AWS-Parameters-and-Secrets-Lambda-Extension:23"
  }

  parameters_and_secrets_layer_arn = lookup(
    local.parameters_and_secrets_layer_arns,
    data.aws_region.current.region,
    null,
  )
}
