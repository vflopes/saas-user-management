output "user_pool_id" {
  description = "The ID of the Cognito User Pool"
  value       = aws_cognito_user_pool.user_pool.id
}

output "frontend_client_id" {
  description = "The ID of the Cognito User Pool Client for the frontend"
  value       = aws_cognito_user_pool_client.frontend_client.id
}
