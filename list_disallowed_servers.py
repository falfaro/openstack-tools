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
list_disallowed_servers.py is a Python tool that relies on the OpenStack
API to gather a list of servers (virtual machines, instances) that violate
the policy defined for the production OpenStack environment.
"""

import collections
import os
import sys

from keystoneclient.v2_0 import client as kc_client
from novaclient import client as cs_client

# Tenants to exclude
EXCLUDED_TENANT_IDS = [
  u'19574184bf104b098cc1d52432574e6a',  # DSM-L
  u'6e0ea662bfab4af89545016b05bb366b',  # DSMC-Monit
  u'1320352435ef4aa682cd15fcb441e812',  # IOT-L
  u'2a2a4cbeb8e3450b9f31ab97a5b5af06',  # admin
  u'8e05b17a9c47418796116f87632f67e5',  # JetSetMe
  u'161e21850d7f468688ade0411ab3dc24',  # service
  ]

os_username = os.environ['OS_USERNAME']
os_password = os.environ['OS_PASSWORD']
os_tenant_name = os.environ['OS_TENANT_NAME']
os_auth_url = os.environ['OS_AUTH_URL']
os_cacert = os.environ['OS_CACERT']


def get_all_tenants():
  """Retrieves a dict mapping tetant ids to tenant names."""

  kc = kc_client.Client(
    username=os_username, password=os_password,
    tenant_name=os_tenant_name, auth_url=os_auth_url, cacert=os_cacert)
  tenants = {}
  for tenant in kc.tenants.list():
    tenants[tenant.id] = tenant.name
  return tenants


def get_servers(excluded_tenant_ids):
  """Returns a dict wit servers filtered out, keyed by user id.

  Builds and returns a dict keyed by user id, where the associated value
  is a list of servers owned by that user, excluding those belonging to
  any of the tenant IDs specified by the @excluded_tenant_ids argument.

  Args:
    excluded_tenant_ids: list, tenant_ids to exclude.

  Returns:
    A dict of user id to list, where each list element is a tuple
    <server name, tenant name>
  """
  cs = cs_client.Client(
    '1.1', os_username, os_password, os_tenant_name, auth_url=os_auth_url,
    cacert=os_cacert)

  servers = collections.defaultdict(list)
  tenants = get_all_tenants()
  search_opts = {
    'all_tenants': True,
    }

  for server in cs.servers.list(search_opts=search_opts):
    if server.tenant_id in excluded_tenant_ids:
      continue
    tenant_name = tenants.get(server.tenant_id, '?')
    servers[server.user_id].append((server.name, tenant_name))
  return servers


def print_servers(servers):
  """Prints the list of servers, grouped by user ID."""

  def _print_server(server):
    server_name, tenant_name = server
    print '    %-35s %-35s' % (server_name, tenant_name)

  print 'user_id'
  _print_server(('server_name', 'tenant_name'))
  print '-'*80
  for user_id, user_servers in servers.iteritems():
    print user_id
    for user_server in user_servers:
      _print_server(user_server)


def main():
  servers = get_servers(EXCLUDED_TENANT_IDS)
  print_servers(servers)


if __name__ == "__main__":
    sys.exit(main())
