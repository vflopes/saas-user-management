data "aws_iam_policy_document" "cognito_cleanup_state_machine_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "cognito_cleanup_state_machine" {
  name               = "cognito-cleanup-state-machine"
  assume_role_policy = data.aws_iam_policy_document.cognito_cleanup_state_machine_assume.json
  path               = "/service/"
}

data "aws_iam_policy_document" "cognito_cleanup_state_machine" {
  statement {
    effect = "Allow"
    actions = [
      "lambda:InvokeFunction"
    ]
    resources = [
      aws_lambda_function.cognito_lambdas["cleanup-list-unverified"].arn,
      aws_lambda_function.cognito_lambdas["cleanup-delete-unverified"].arn,
    ]
  }
}

resource "aws_iam_policy" "cognito_cleanup_state_machine" {
  name   = "cognito-cleanup-state-machine"
  path   = "/service/"
  policy = data.aws_iam_policy_document.cognito_cleanup_state_machine.json
}

resource "aws_iam_role_policy_attachment" "cognito_cleanup_state_machine" {
  role       = aws_iam_role.cognito_cleanup_state_machine.name
  policy_arn = aws_iam_policy.cognito_cleanup_state_machine.arn
}

resource "aws_sfn_state_machine" "cognito_cleanup_state_machine" {
  name     = "cognito-cleanup-unverified"
  role_arn = aws_iam_role.cognito_cleanup_state_machine.arn

  definition = jsonencode({
    Comment = "Delete Cognito users that remain unverified after the grace period"
    StartAt = "ListPage"
    States = {
      ListPage = {
        Type       = "Task"
        Resource   = aws_lambda_function.cognito_lambdas["cleanup-list-unverified"].arn
        ResultPath = "$.listing"
        Parameters = {
          "next_token.$" = "$.next_token"
        }
        Retry = [
          {
            ErrorEquals     = ["States.ALL"]
            IntervalSeconds = 2
            BackoffRate     = 2.0
            MaxAttempts     = 3
          }
        ]
        Next = "ProcessUsers"
      }
      ProcessUsers = {
        Type           = "Map"
        ItemsPath      = "$.listing.users"
        ResultPath     = null
        MaxConcurrency = 5
        Iterator = {
          StartAt = "CleanupUser"
          States = {
            CleanupUser = {
              Type       = "Task"
              Resource   = aws_lambda_function.cognito_lambdas["cleanup-delete-unverified"].arn
              ResultPath = null
              Retry = [
                {
                  ErrorEquals     = ["States.ALL"]
                  IntervalSeconds = 2
                  BackoffRate     = 2.0
                  MaxAttempts     = 3
                }
              ]
              End = true
            }
          }
        }
        Next = "HasNextPage"
      }
      HasNextPage = {
        Type = "Choice"
        Choices = [
          {
            Variable   = "$.listing.next_token"
            IsPresent  = true
            Next       = "PrepareNextPage"
          }
        ]
        Default = "Done"
      }
      PrepareNextPage = {
        Type       = "Pass"
        ResultPath = "$"
        Result = {
          "next_token.$" = "$.listing.next_token"
        }
        Next = "ListPage"
      }
      Done = {
        Type = "Succeed"
      }
    }
  })
}

resource "aws_lambda_permission" "cognito_cleanup_allow_state_machine_list" {
  statement_id  = "AllowExecutionFromStateMachineList"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cognito_lambdas["cleanup-list-unverified"].function_name
  principal     = "states.amazonaws.com"
  source_arn    = aws_sfn_state_machine.cognito_cleanup_state_machine.arn
}

resource "aws_lambda_permission" "cognito_cleanup_allow_state_machine_delete" {
  statement_id  = "AllowExecutionFromStateMachineDelete"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cognito_lambdas["cleanup-delete-unverified"].function_name
  principal     = "states.amazonaws.com"
  source_arn    = aws_sfn_state_machine.cognito_cleanup_state_machine.arn
}

resource "aws_cloudwatch_event_rule" "cognito_cleanup_schedule" {
  name                = "cognito-cleanup-unverified-schedule"
  schedule_expression = "cron(0 0,12 * * ? *)"
}

data "aws_iam_policy_document" "cognito_cleanup_scheduler_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "cognito_cleanup_scheduler" {
  name               = "cognito-cleanup-scheduler"
  assume_role_policy = data.aws_iam_policy_document.cognito_cleanup_scheduler_assume.json
  path               = "/service/"
}

data "aws_iam_policy_document" "cognito_cleanup_scheduler" {
  statement {
    effect = "Allow"
    actions = [
      "states:StartExecution"
    ]
    resources = [aws_sfn_state_machine.cognito_cleanup_state_machine.arn]
  }
}

resource "aws_iam_role_policy" "cognito_cleanup_scheduler" {
  role   = aws_iam_role.cognito_cleanup_scheduler.id
  policy = data.aws_iam_policy_document.cognito_cleanup_scheduler.json
}

resource "aws_cloudwatch_event_target" "cognito_cleanup_schedule_target" {
  rule      = aws_cloudwatch_event_rule.cognito_cleanup_schedule.name
  target_id = "cognito-cleanup-unverified"
  arn       = aws_sfn_state_machine.cognito_cleanup_state_machine.arn
  role_arn  = aws_iam_role.cognito_cleanup_scheduler.arn
}
