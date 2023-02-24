variable "project" {
  description = "Project name. It should be the same as repo name. The value comes from PROJECT in .env file."
}

variable "workspace_tag" {
  description = "The tag value for the \"Workspace\". If it's user workspace then the pattern must be \"user_<short_code>. If it's PR then it must be pr_<pr_no>. Otherwise it's either \"dev\" or \"prod\""
}

variable "account_zone" {
  description = "It's the root zone name of the account"
}

variable "service_dependency_workspace" {
  description = "The default workspace when we use an external service terraform state to get outputs and other parameters"
}

variable "sd_vajeh_auth_workspace" {
  description = "vajeh-auth workspace to use"
  default     = ""
}

locals {
  vajeh_auth_workspace = var.sd_vajeh_auth_workspace == "" ? var.service_dependency_workspace : var.sd_vajeh_auth_workspace
}
