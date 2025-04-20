resource "iosxe_mdt_subscription" "cpu_subs" {
  for_each               = var.cpu_subscriptions
  subscription_id        = each.key
  stream                 = "yang-push"
  encoding               = "encode-kvgpb"
  update_policy_periodic = var.cpu_periodic
  source_address         = var.source_address
  filter_xpath           = each.value.xpath
  receivers = [
    {
      address  = var.receiver_ip
      port     = var.receiver_port
      protocol = "grpc-tcp"
    }
  ]
}