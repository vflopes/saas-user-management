data "aws_ssm_parameter" "ses_root_domain_identity_arn" {
  name = "/saas-infrastructure/production/ses_root_domain_identity_arn"
}

data "aws_ssm_parameter" "user_management" {
  for_each = toset([
    "user_management_event_bus_arn",
    "user_management_users_table_name",
    "user_management_users_table_arn",
    "user_management_users_table_stream_arn",
  ])
  name = "/saas-infrastructure/production/${each.key}"
}

locals {
  user_management_event_bus_arn          = data.aws_ssm_parameter.user_management["user_management_event_bus_arn"].value
  user_management_users_table_stream_arn = data.aws_ssm_parameter.user_management["user_management_users_table_stream_arn"].value
  user_management_users_table_arn        = data.aws_ssm_parameter.user_management["user_management_users_table_arn"].value
}

data "aws_ssm_parameter" "api_gateway_id" {
  name = "/saas-infrastructure/production/api_gateway_id"
}
