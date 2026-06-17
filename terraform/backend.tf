#terraform/backend.tf



resource "aws_s3_bucket" "tfstate" {
    bucket = "ai-devops-tfstate-${var.project_name}"

    lifecycle {
      prevent_destroy = true
    }

    tags = {
        Project = var.project_name
    }

}


resource "aws_s3_bucket_versioning" "tfstate" {

    bucket = aws_s3_bucket.tfstate.id

    versioning_configuration {
        status = "Enabled"
    }
}


resource "aws_dynamodb_table" "tflock" {
    name         = "terraform-lock"
    billing_mode = "PAY_PER_REQUEST"
    hash_key     = "LockID"

    attribute {
        name = "LockID"
        type = "S"
    }

    tags = {
        Project = var.project_name
    }
}