resource "aws_apigatewayv2_api" "vajeh_api" {
  name          = local.prefix
  protocol_type = "HTTP"
  body          = templatefile("./oas/vajeh-api.yaml", {})
}

