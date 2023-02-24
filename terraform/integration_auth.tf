data "terraform_remote_state" "vajeh-auth" {
  backend = "s3"

  config = {
    bucket = "vajeh-auth-ptl-terraform-state"
    key    = "env:/${local.workspace}/state"
    region = "eu-west-2"
  }
}

locals {
  issuer        = "https://${data.terraform_remote_state.vajeh-auth.outputs.user_pool_endpoint}"
  scopes        = data.terraform_remote_state.vajeh-auth.outputs.test_client_scopes
  test_audience = data.terraform_remote_state.vajeh-auth.outputs.test_client_id
}
