data "aws_iam_policy_document" "user_management_sign_up_lambda_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "user_management_sign_up" {
  name               = "user-management-sign-up-api"
  assume_role_policy = data.aws_iam_policy_document.user_management_sign_up_lambda_assume.json
  path               = "/service/"
}

resource "aws_iam_role_policy_attachment" "user_management_sign_up_logging" {
  role       = aws_iam_role.user_management_sign_up.name
  policy_arn = var.lambda_logging_arn
}

resource "aws_lambda_function" "user_management_sign_up" {
  filename      = "${path.module}/../dummy_lambda.zip"
  runtime       = "python3.13"
  handler       = "index.handler"
  function_name = "user-management-sign-up-api"
  role          = aws_iam_role.user_management_sign_up.arn
  memory_size   = 128
  timeout       = 10

  logging_config {
    log_format            = "JSON"
    application_log_level = "INFO"
    system_log_level      = "WARN"
  }

  lifecycle {
    ignore_changes = [
      runtime,
      handler,
    ]
  }
}

resource "aws_apigatewayv2_integration" "user_management_sign_up" {
  api_id           = var.api_gateway_id
  integration_type = "AWS_PROXY"

  connection_type        = "INTERNET"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.user_management_sign_up.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "user_management_sign_up" {
  api_id    = var.api_gateway_id
  route_key = "ANY /sign-up/{proxy+}"

  target = "integrations/${aws_apigatewayv2_integration.user_management_sign_up.id}"
}
