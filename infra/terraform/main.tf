terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "GCP project that hosts the Rodex platform."
  type        = string
}

variable "region" {
  description = "Default region for deployed resources."
  type        = string
  default     = "us-central1"
}

# TODO: add secret manager, logging sinks, and network modules.
