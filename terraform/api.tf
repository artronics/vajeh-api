locals {
  oas_vars = {
    api_url             = local.api_domain_name
    region              = data.aws_region.current.name
    lambda_identity_arn = aws_lambda_function.app.arn
  }
}

resource "aws_apigatewayv2_api" "vajeh_api" {
  name          = local.prefix
  protocol_type = "HTTP"
  body          = templatefile("./oas/vajeh-api.yaml", local.oas_vars)
}

output "oas" {
  value = aws_apigatewayv2_api.vajeh_api.body //templatefile("./oas/vajeh-api.yaml", local.oas_vars)
}

resource "aws_apigatewayv2_stage" "default_stage" {
  api_id      = aws_apigatewayv2_api.vajeh_api.id
  name        = local.workspace
  auto_deploy = true
}

resource "aws_apigatewayv2_api_mapping" "api_domain_map" {
  api_id      = aws_apigatewayv2_api.vajeh_api.id
  domain_name = aws_apigatewayv2_domain_name.service_api_domain_name.domain_name
  stage       = aws_apigatewayv2_stage.default_stage.name
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.app.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.vajeh_api.execution_arn}/*/*"
}
