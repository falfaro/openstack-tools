#!/usr/bin/python
# Copyright 2014 Felipe Alfaro Solana
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
list_invalid_subnets.py is a Python tool that relies on the OpenStack API to
gather a list of subnets that are incorrectly defined or configured (e.g.
subnets whose gateway IP lies outside their CIDR).
"""

import netaddr
import os

from neutronclient.v2_0 import client

os_username = os.environ['OS_USERNAME']
os_password = os.environ['OS_PASSWORD']
os_tenant_name = os.environ['OS_TENANT_NAME']
os_auth_url = os.environ['OS_AUTH_URL']
os_cacert = os.environ['OS_CACERT']

neutron = client.Client(username=os_username,
                        password=os_password,
                        tenant_name=os_tenant_name,
                        auth_url=os_auth_url,
                        ca_cert=os_cacert)

subnets = neutron.list_subnets()
for subnet in subnets['subnets']:
    if not subnet['gateway_ip']:
        continue
    id = subnet['id']
    cidr = netaddr.IPNetwork(subnet['cidr'])
    gateway_ip = netaddr.IPAddress(subnet['gateway_ip'])
    if gateway_ip not in cidr:
        print 'subnet: %s gateway: %s CIDR: %s' % (
            id, cidr, gateway_ip)
