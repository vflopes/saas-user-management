data "aws_iam_policy_document" "user_management_bus_processor_lambda_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "user_management_bus_processor" {
  name               = "user-management-bus-processor"
  assume_role_policy = data.aws_iam_policy_document.user_management_bus_processor_lambda_assume.json
  path               = "/service/"
}

resource "aws_iam_role_policy_attachment" "user_management_bus_processor_logging" {
  role       = aws_iam_role.user_management_bus_processor.name
  policy_arn = data.aws_iam_policy.lambda_logging.arn
}

data "aws_iam_policy_document" "user_management_bus_processor" {
  statement {
    effect = "Allow"
    actions = [
      "cognito-idp:AdminDeleteUser",
    ]
    resources = [aws_cognito_user_pool.user_pool.arn]
  }
}

resource "aws_iam_policy" "user_management_bus_processor" {
  name   = "user-management-bus-processor"
  path   = "/service/"
  policy = data.aws_iam_policy_document.user_management_bus_processor.json
}

resource "aws_iam_role_policy_attachment" "user_management_bus_processor" {
  role       = aws_iam_role.user_management_bus_processor.name
  policy_arn = aws_iam_policy.user_management_bus_processor.arn
}

resource "aws_lambda_function" "user_management_bus_processor" {
  filename      = "${path.module}/dummy_lambda.zip"
  runtime       = "python3.13"
  handler       = "index.handler"
  function_name = "user-management-bus-processor"
  role          = aws_iam_role.user_management_bus_processor.arn
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

resource "aws_cloudwatch_event_rule" "user_management_bus_processor" {
  name           = "user-management-bus-processor"
  event_bus_name = local.user_management_event_bus_arn
  event_pattern = jsonencode({
    "source" : ["saas.user-management.users-table"],
    "detail-type" : ["DynamoDB Stream Record"],
  })
}

resource "aws_cloudwatch_event_target" "user_management_bus_processor" {
  rule           = aws_cloudwatch_event_rule.user_management_bus_processor.name
  target_id      = "user-management-bus-processor"
  arn            = aws_lambda_function.user_management_bus_processor.arn
  event_bus_name = local.user_management_event_bus_arn
}

resource "aws_lambda_permission" "allow_eventbridge_to_invoke_user_management_bus_processor" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.user_management_bus_processor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.user_management_bus_processor.arn
}
