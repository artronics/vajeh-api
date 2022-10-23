locals {
  project = "vajeh"
  tier    = "api"
}

locals {
  environment = terraform.workspace
  service = "api"
  name_prefix = "${local.project}-${local.service}-${local.environment}"
}

locals {
  root_domain_name = "vajeh.artronics.me.uk"
  domain_name = "${local.environment}.${local.service}.${local.root_domain_name}"
}
