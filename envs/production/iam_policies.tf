data "aws_iam_policy" "lambda_logging" {
  path_prefix = "/service/"
  name        = "lambda-logging"
}
