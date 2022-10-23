terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4"
    }
  }

  backend "s3" {
    bucket = "terraform-vajeh-api"
    key = "state"
    region = "eu-west-2"
  }
}

provider "aws" {
  region = "eu-west-2"

  default_tags {
    tags = {
      project     = local.project
      environment = local.environment
      tier        = local.tier
    }
  }
}

provider "aws" {
  alias  = "main"
  region = "eu-west-2"
  default_tags {
    tags = {
      project     = local.project
      environment = local.environment
      tier        = local.tier
    }
  }
}

provider "aws" {
  alias  = "acm_provider"
  region = "us-east-1"
  default_tags {
    tags = {
      project     = local.project
      environment = local.environment
      tier        = local.tier
    }
  }
}
