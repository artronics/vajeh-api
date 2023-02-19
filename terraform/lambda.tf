resource "aws_lambda_function" "app" {
  function_name    = "${local.prefix}-api-test"
  filename         = "nametest.zip"
  source_code_hash = data.archive_file.python_lambda_package.output_base64sha256
  role             = aws_iam_role.lambda_exec.arn
  runtime          = "python3.8"
  handler          = "test.lambda_handler"
  timeout          = 10
}

data "archive_file" "python_lambda_package" {
  type        = "zip"
  source_file = "${path.module}/test.py"
  output_path = "nametest.zip"
}

resource "aws_iam_role" "lambda_exec" {
  name = "${local.prefix}-serverless_lambda"

  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Sid       = ""
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}
