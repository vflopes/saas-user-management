locals {
  root_domain = "saas.vflopes.com"
}

terraform {
  backend "s3" {
    bucket       = "tfstate-31115663950920251219185056487700000001"
    key          = "saas-user-management/production.tfstate"
    region       = "us-east-1"
    use_lockfile = true
  }


  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.27.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "3.7.2"
    }
  }
}

provider "aws" {}

data "aws_caller_identity" "current" {}

provider "random" {}
