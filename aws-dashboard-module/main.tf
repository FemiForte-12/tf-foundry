resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = var.dashboard_name
  dashboard_body = jsonencode({
    widgets = [
      for widget in var.widgets : {
        type       = widget.type
        x          = widget.x
        y          = widget.y
        width      = widget.width
        height     = widget.height
        properties = widget.properties
      }
    ]
  })
} 