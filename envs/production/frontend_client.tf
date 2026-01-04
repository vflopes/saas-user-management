
resource "aws_cognito_user_pool_client" "frontend_client" {
  name         = "web-client"
  user_pool_id = aws_cognito_user_pool.user_pool.id

  generate_secret = false

  supported_identity_providers = ["COGNITO"]

  explicit_auth_flows = [
    "ALLOW_CUSTOM_AUTH",
    "ALLOW_USER_AUTH"
  ]

  prevent_user_existence_errors        = "ENABLED"
  allowed_oauth_flows_user_pool_client = true

  allowed_oauth_flows = ["code"]
  allowed_oauth_scopes = [
    "phone",
    "email",
    "openid",
    "profile",
  ]

  callback_urls = [
    "https://${local.root_domain}/callback",
    "http://localhost:3000/callback",
  ]

  logout_urls = [
    "https://${local.root_domain}/logout",
    "http://localhost:3000/logout",
  ]

  refresh_token_rotation {
    feature                    = "ENABLED"
    retry_grace_period_seconds = 0
  }

  enable_token_revocation = true

  auth_session_validity = 5

  access_token_validity  = 15
  id_token_validity      = 1
  refresh_token_validity = 10

  token_validity_units {
    access_token  = "minutes"
    id_token      = "hours"
    refresh_token = "days"
  }
}
