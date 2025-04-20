# validate_subscriptions.tf
data "iosxe_mdt_subscription" "example100" {
  subscription_id = 100
}

data "iosxe_mdt_subscription" "example101" {
  subscription_id = 101
}

data "iosxe_mdt_subscription" "example102" {
  subscription_id = 102
}

data "iosxe_mdt_subscription" "example103" {
  subscription_id = 103
}

data "iosxe_mdt_subscription" "example104" {
  subscription_id = 104
}