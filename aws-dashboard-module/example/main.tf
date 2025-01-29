module "cloudwatch_dashboard" {
  source = "../aws-dashboard-module"

  dashboard_name = "my-application-dashboard"
  
  widgets = {
    cpu_utilization = {
      type   = "metric"
      x      = 0
      y      = 0
      width  = 12
      height = 6
      properties = {
        metrics = [
          ["AWS/EC2", "CPUUtilization", "InstanceId", "i-1234567890abcdef0"]
        ]
        period = 300
        stat   = "Average"
        region = "us-west-2"
        title  = "EC2 CPU Utilization"
      }
    },
    memory_usage = {
      type   = "metric"
      x      = 12
      y      = 0
      width  = 12
      height = 6
      properties = {
        metrics = [
          ["AWS/EC2", "MemoryUtilization", "InstanceId", "i-1234567890abcdef0"]
        ]
        period = 300
        stat   = "Average"
        region = "us-west-2"
        title  = "EC2 Memory Usage"
      }
    }
  }
} 