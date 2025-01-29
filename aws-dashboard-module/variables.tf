variable "dashboard_name" {
  description = "Name of the dashboard"
  type        = string
}

variable "widgets" {
  description = "Map of widgets to be placed on the dashboard"
  type = map(object({
    type   = string
    x      = number
    y      = number
    width  = number
    height = number
    properties = object({
      metrics  = optional(list(list(string))) # For metric widgets
      alarms   = optional(list(string))       # For alarm widgets
      markdown = optional(string)             # For text/markdown widgets
      view     = optional(string)             # Widget view type (e.g., "timeSeries", "singleValue")
      region   = optional(string)             # AWS region
      period   = optional(number)             # Metric period in seconds
      stat     = optional(string)             # Statistic type (e.g., "Average", "Sum")
      title    = optional(string)             # Widget title
      stacked  = optional(bool)               # For stacked metrics
    })
  }))
} 