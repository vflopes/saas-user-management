locals {
  cognito_lambdas = {
    pre-sign-up-trigger = {
      environment_vars = tomap({
        PARAMETERS_SECRETS_EXTENSION_LOG_LEVEL = "INFO"
        POWERTOOLS_LOG_LEVEL                   = "INFO"
        POWERTOOLS_SERVICE_NAME                = "pre-sign-up-trigger"
        # APP_RECAPTCHA__SECRET_KEY                        = "/saas-manual-inputs/recaptcha/secret-key"
        APP_USERS_TABLE__NAME                            = data.aws_ssm_parameter.user_management["user_management_users_table_name"].value
        APP_USERS_TABLE__EXPIRE_UNVERIFIED_USERS_MINUTES = "360"
      })
    },
    post-confirmation-trigger = {
      environment_vars = tomap({
        PARAMETERS_SECRETS_EXTENSION_LOG_LEVEL = "INFO"
        POWERTOOLS_LOG_LEVEL                   = "INFO"
        POWERTOOLS_SERVICE_NAME                = "post-confirmation-trigger"
        APP_PHOSTHOG__API_KEY                  = "/saas-manual-inputs/posthog/api-key"
        APP_PHOSTHOG__API_HOST                 = "/saas-manual-inputs/posthog/api-host"
      })
    },
  }

  cognito_lambdas_keys = toset(keys(local.cognito_lambdas))
}

data "aws_iam_policy_document" "cognito_lambdas_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "cognito_lambdas" {
  path               = "/service/"
  name               = "cognito-lambdas"
  assume_role_policy = data.aws_iam_policy_document.cognito_lambdas_assume_role.json
}

resource "aws_iam_role_policy_attachment" "cognito_lambdas_lambda_logging" {
  role       = aws_iam_role.cognito_lambdas.name
  policy_arn = data.aws_iam_policy.lambda_logging.arn
}

resource "aws_iam_policy" "cognito_lambdas" {
  path        = "/service/"
  name        = "cognito-lambdas"
  description = "IAM policy for cognito lambdas"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "kms:Decrypt",
          "cognito-idp:AdminDeleteUser",
          "cognito-idp:ListUsers",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
        ]
        Resource = data.aws_ssm_parameter.user_management["user_management_users_table_arn"].value
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "cognito_lambdas" {
  role       = aws_iam_role.cognito_lambdas.name
  policy_arn = aws_iam_policy.cognito_lambdas.arn
}

resource "aws_lambda_function" "cognito_lambdas" {

  for_each = local.cognito_lambdas_keys

  filename      = "${path.module}/dummy_lambda.zip"
  runtime       = "python3.13"
  handler       = "index.handler"
  function_name = "cognito-${each.key}"
  role          = aws_iam_role.cognito_lambdas.arn
  memory_size   = 256
  timeout       = 5

  layers = [
    local.parameters_and_secrets_layer_arn,
  ]

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

  dynamic "environment" {
    for_each = lookup(local.cognito_lambdas[each.key], "environment_vars", {}) != {} ? [1] : []
    content {
      variables = local.cognito_lambdas[each.key]["environment_vars"]
    }
  }

}

resource "aws_lambda_permission" "cognito_lambda_allow_user_pool" {
  for_each      = local.cognito_lambdas_keys
  statement_id  = "AllowExecutionFromCognitoUserPool"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cognito_lambdas[each.key].function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = aws_cognito_user_pool.user_pool.arn
}
