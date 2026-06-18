resource "aws_codestarconnections_connection" "github" {
    name = "${var.project_name}-github"
    provider_type = "GitHub"

    tags = {
        Project = var.project_name
    }

}

# S3 pentru artifacts CodePipeline

resource "aws_s3_bucket" "pipelien_artifacts" {

    bucket = "${var.project_name}-pipeline-artifacts"
    force_destroy = true

    tags = {

        Project = var.project_name
    }
}

# IAM role pentru CodePipeline

resource "aws_iam_role" "codepipeline" {
    name = "${var.project_name}-codepipeline-role"
    
    assume_role_policy = jsonencode ({
        Version = "2012-10-17"
        Statement = [{
            Action = "sts:AssumeRole"
            Effect = "Allow"
            Principal = { Service = "codepipeline.amazonaws.com"}
        }]
    })
}

resource "aws_iam_role_policy" "codepipeline" {
  name = "${var.project_name}-codepipeline-policy"
  role = aws_iam_role.codepipeline.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:GetBucketVersioning"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "codebuild:BatchGetBuilds",
          "codebuild:StartBuild"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "codestar-connections:UseConnection"
        ]
        Resource = "arn:aws:codestar-connections:eu-west-1:176376307636:connection/23d19c0d-9736-4397-922a-fc7482feb485"
      }
    ]
  })
}

# IAM role pentru CodeBuild

resource "aws_iam_role" "codebuild" {
    name = "${var.project_name}-codebuild-role"

    assume_role_policy = jsonencode ({
        Version = "2012-10-17"
        Statement = [{
            Action = "sts:AssumeRole"
            Effect = "Allow"
            Principal = { Service = "codebuild.amazonaws.com"}
        }]
    })
}

resource "aws_iam_role_policy" "codebuild" {
    name = "${var.project_name}-codebuild-policy"
    role = aws_iam_role.codebuild.id

    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
        {
            Effect = "Allow" 
            Action = [
                "logs:CreateLogsGroup", 
                "logs:CreateLogStream", 
                "logs:PutLogEvent"
            ]
            Resource = "*"


        },
        {
            Effect = "Allow" 
            Action = [  "s3:GetObject",
                        "s3:PutObject",
                        "s3:GetBUcketVersioning"
                    ]
            Resource = "*"
        },
        {   
            Effect = "Allow" 
            Action = [ "ssm: GetParameter"  ]
            Resource = "arn:aws:ssm:eu-west-1:*:parameter/ai-devops-assistant/*"
        },
        {
            Effect = "Allow"
            Action = "*"
            Resource = "*"
        }
        ]

    })

}

# CodeBuild project

resource "aws_codebuild_project" "terraform" {
    name = "${var.project_name}-build"
    service_role = aws_iam_role.codebuild.arn
    build_timeout = 30

    artifacts {
        type = "CODEPIPELINE"
    }

    environment {
        compute_type = "BUILD_GENERAL1_SMALL"
        image = "aws/codebuild/standard:7.0"
        type = "LINUX_CONTAINER"

        environment_variable {
            name = "TF_VERSION"
            value = "1.9.0"
        }
    }

    source {
        type = "CODEPIPELINE"
        buildspec = "buildspec.yml"
    }

    tags = {
        Project = var.project_name
    }
}

# CodePipeline

resource "aws_codepipeline" "main" {
        name = "${var.project_name}-pipeline"
        role_arn = aws_iam_role.codepipeline.arn

        artifact_store {
            location = aws_s3_bucket.pipelien_artifacts.bucket
            type = "S3"

        }

    stage {
        name = "Source"
        action {
            name             = "GitHub"
            category         = "Source"
            owner            = "AWS"
            provider         = "CodeStarSourceConnection"
            version          = "1"
            output_artifacts = ["source_output"]

            configuration = {
                ConnectionArn    = aws_codestarconnections_connection.github.arn
                FullRepositoryId = "cr1stiaaana/ai-devops-assistant"
                BranchName       = "main"
            }
    }
  }

    stage {
        name = "Build"
        action {
            name = "TerraformApply"
            category = "Build"
            owner = "AWS"
            provider = "CodeBuild"
            version = "1"
            input_artifacts = ["source_output"]
            configuration = {
                ProjectName = aws_codebuild_project.terraform.name
            }
        }
    }
    

    tags = {
        Project = var.project_name
    }



}