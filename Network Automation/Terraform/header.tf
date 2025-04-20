terraform {
  required_providers {
    iosxe = {
      source  = "CiscoDevNet/iosxe"
      version = ">= 0.3.3"
    }
  }
}

provider "iosxe" {
  username = "tmaco"
  password = "cisco"
  url      = "https://10.10.40.1"
}
