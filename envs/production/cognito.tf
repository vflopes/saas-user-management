resource "random_uuid" "cognito_external_id" {
}

data "aws_iam_policy_document" "cognito_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["cognito-idp.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "sts:ExternalId"

      values = [random_uuid.cognito_external_id.result]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"

      values = [data.aws_caller_identity.current.account_id]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"

      values = ["arn:aws:cognito-idp:*:${data.aws_caller_identity.current.account_id}:userpool/*"]
    }
  }
}

resource "aws_iam_role" "cognito_role" {
  path               = "/service/"
  name               = "cognito-user-pool"
  assume_role_policy = data.aws_iam_policy_document.cognito_assume_role_policy.json
}

data "aws_iam_policy_document" "cognito_role_policy" {
  statement {
    sid     = "AllowSNSPublish"
    effect  = "Allow"
    actions = ["sns:Publish"]
    resources = [
      "*",
    ]
  }
}

resource "aws_iam_policy" "cognito_role_policy" {
  path   = "/service/"
  name   = "cognito-user-pool"
  policy = data.aws_iam_policy_document.cognito_role_policy.json
}

resource "aws_iam_role_policy_attachment" "cognito_role_policy_attachment" {
  role       = aws_iam_role.cognito_role.name
  policy_arn = aws_iam_policy.cognito_role_policy.arn
}

resource "aws_cognito_user_pool" "user_pool" {
  name = "application-user-pool"

  user_pool_tier = "ESSENTIALS"

  username_configuration {
    case_sensitive = false
  }

  alias_attributes         = ["email", "phone_number", "preferred_username"]
  auto_verified_attributes = ["email", "phone_number"]

  user_attribute_update_settings {
    attributes_require_verification_before_update = ["email", "phone_number"]
  }

  admin_create_user_config {
    allow_admin_create_user_only = false
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
    recovery_mechanism {
      name     = "verified_phone_number"
      priority = 2
    }
  }

  sign_in_policy {
    allowed_first_auth_factors = [
      "PASSWORD",
      "WEB_AUTHN"
    ]
  }

  password_policy {
    minimum_length                   = 8
    require_lowercase                = true
    require_uppercase                = true
    require_numbers                  = true
    require_symbols                  = true
    temporary_password_validity_days = 7
  }


  mfa_configuration = "OPTIONAL"

  software_token_mfa_configuration {
    enabled = true
  }

  web_authn_configuration {
    user_verification = "required"
  }

  email_configuration {
    email_sending_account = "DEVELOPER"
    source_arn            = data.aws_ssm_parameter.ses_root_domain_identity_arn.value
    from_email_address    = "Accounts and Access <noreply@${local.root_domain}>"
  }

  sms_configuration {
    external_id    = random_uuid.cognito_external_id.result
    sns_caller_arn = aws_iam_role.cognito_role.arn
  }

  schema {
    attribute_data_type      = "String"
    name                     = "email"
    required                 = true
    mutable                  = true
    developer_only_attribute = false
  }

  schema {
    attribute_data_type      = "String"
    name                     = "phone_number"
    required                 = false
    mutable                  = true
    developer_only_attribute = false
  }

  schema {
    attribute_data_type      = "String"
    name                     = "preferred_username"
    required                 = true
    mutable                  = true
    developer_only_attribute = false
    string_attribute_constraints {
      min_length = 2
      max_length = 24
    }
  }

  schema {
    attribute_data_type      = "String"
    name                     = "nickname"
    required                 = false
    mutable                  = true
    developer_only_attribute = false
    string_attribute_constraints {
      max_length = 32
    }
  }

  schema {
    attribute_data_type      = "String"
    name                     = "custom:role"
    required                 = false
    mutable                  = true
    developer_only_attribute = true
  }
}

# resource "aws_cognito_user_pool_client" "this" {
#   name         = "${local.app_name}-production-client"
#   user_pool_id = aws_cognito_user_pool.this.id

#   generate_secret = false

#   supported_identity_providers = ["COGNITO"]

#   explicit_auth_flows = [
#     "ALLOW_REFRESH_TOKEN_AUTH",
#     "ALLOW_USER_PASSWORD_AUTH",
#     "ALLOW_USER_SRP_AUTH",
#     "ALLOW_CUSTOM_AUTH"
#   ]

#   prevent_user_existence_errors = "ENABLED"
#   enable_token_revocation       = true
#   auth_session_validity         = 3

#   access_token_validity  = 60
#   id_token_validity      = 60
#   refresh_token_validity = 30

#   token_validity_units {
#     access_token  = "minutes"
#     id_token      = "minutes"
#     refresh_token = "days"
#   }
# }
