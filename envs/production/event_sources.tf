data "aws_iam_policy_document" "user_events_pipe_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["pipes.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "user_events_pipe" {
  name               = "user-management-events-pipe"
  assume_role_policy = data.aws_iam_policy_document.user_events_pipe_assume.json
  path               = "/service/"
}

data "aws_iam_policy_document" "user_events_pipe" {
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:DescribeStream",
      "dynamodb:GetRecords",
      "dynamodb:GetShardIterator",
      "dynamodb:ListStreams",
    ]
    resources = [local.user_management_users_table_stream_arn]
  }

  statement {
    effect = "Allow"
    actions = [
      "events:PutEvents",
    ]
    resources = [local.user_management_event_bus_arn]
  }
}

resource "aws_iam_policy" "user_events_pipe" {
  name   = "user-management-events-pipe"
  path   = "/service/"
  policy = data.aws_iam_policy_document.user_events_pipe.json
}

resource "aws_iam_role_policy_attachment" "user_events_pipe" {
  role       = aws_iam_role.user_events_pipe.name
  policy_arn = aws_iam_policy.user_events_pipe.arn
}

resource "aws_pipes_pipe" "user_events" {
  name     = "user-management-users-stream"
  role_arn = aws_iam_role.user_events_pipe.arn
  source   = local.user_management_users_table_stream_arn
  target   = local.user_management_event_bus_arn

  source_parameters {
    dynamodb_stream_parameters {
      starting_position = "TRIM_HORIZON"
      batch_size        = 10
    }
  }

  target_parameters {
    eventbridge_event_bus_parameters {
      detail_type = "DynamoDB Stream Record"
      source      = "saas.user-management.users-table"
    }
  }
}
