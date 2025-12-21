data "aws_ssm_parameter" "ses_root_domain_identity_arn" {
  name = "/saas-infrastructure/production/ses_root_domain_identity_arn"
}
