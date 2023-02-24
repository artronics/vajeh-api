data "terraform_remote_state" "vajeh-auth" {
  backend = "s3"

  config = {
    bucket = "vajeh-auth-ptl-terraform-state"
    key    = "env:/${local.vajeh_auth_workspace}/state"
    region = "eu-west-2"
  }
}

locals {
  auth_issuer   = "https://${data.terraform_remote_state.vajeh-auth.outputs.user_pool_endpoint}"
  auth_scopes   = data.terraform_remote_state.vajeh-auth.outputs.auth_scopes
  auth_audience = data.terraform_remote_state.vajeh-auth.outputs.client_ids
}
