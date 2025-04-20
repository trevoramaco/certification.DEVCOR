variable source_address {
    type = string
    default = "1.1.1.1"
    description = "Source address"
}

variable receiver_ip {
    type = string
    default = "1.1.1.1"
    description = "Receiver IP"
}

variable receiver_port  {
    type = string
    default = "57500"
    description = "Port to send data to"
}

# CPU.tf
variable cpu_periodic {
    type = string
    default = "100"
    description = "Short update interval"
}

variable "cpu_subscriptions" {
  default = {
    101 = {
      xpath = "/process-cpu-ios-xe-oper:cpu-usage/cpu-utilization/one-minute"
    },
    102 = {
      xpath = "/process-cpu-ios-xe-oper:cpu-usage/cpu-utilization/five-minutes"
    }
  }
}

# XPath.tf
variable "subscriptions" {
  default = {
    103 = {
      xpath = "/environment-ios-xe-oper:environment-sensors"
    },
    104 = {
      xpath = "/interfaces-ios-xe-oper:interfaces"

    }
  }
}

variable example_periodic {
    type = string
    default = "6000"
    description = "Long update interval"
}