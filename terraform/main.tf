# terraform/main.tf

terraform {

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"

    }
}
    # se va activa dupa ce cream S3 + DynamoDB
    backend "s3" {

      bucket         = "ai-devops-tfstate-ai-devops-assistant"
      key            = "terraform.tfstate"
      region         = "eu-west-1"
      use_lockfile   = true
    }
}

provider "aws" {
    region = var.aws_region
}
