terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }

  backend "s3" {
    bucket         = "iot-lab-terraform-state-537124935206"
    key            = "terraform.tfstate"
    region         = "ca-central-1"
    dynamodb_table = "iot-lab-terraform-locks"
    encrypt        = true
  }
}
