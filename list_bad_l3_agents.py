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
list_bad_l3_agents.py is a Python tool that relies on the OpenStack API to
gather a list of Neutron L3 agents that are being reported as bad by Neutron
Server.

This tool reads DEBUG log lines from stdin (usually piped from neutron-server
log files in /var/log/neutron/server.log) to find those L3 agents that are
not reporting their state at the right rate. L3 agents report their state back
to Neutron server every report_interval seconds (defined inside the AGENT
section in /etc/neutron/neutron.conf).
"""

import collections
import datetime
import re
import sys

NEUTRON_BINARY = 'neutron-l3-agent'

# Regular expression used to match DEBUG log lines corresponding to the
# report_state RPC method call
REPORT_STATE_RE = re.compile(r"""
# GROUP 1
(
  \d{4}-\d{2}-\d{2}                    # YYYY-MM-DD
  \s
  \d{2}:\d{2}:\d{2}                    # HH:MM:SS
)
\.\d{3}                                # Miliseconds
\s\d+\sDEBUG\sneutron.openstack.common.rpc.amqp\s\[-\]\sreceived\s
# GROUP 2
(
  {.*u'method':\su\'report_state\'.*}  # Log data (Pytthon dict as str)
)
""", re.VERBOSE)


def is_report_interval(ts1, ts2, report_interval=60, epsilon=1):
  """Returns whether (ts1 - ts2) is less than report_interval seconds."""

  tdelta = abs(ts1 - ts2)
  report_interval = datetime.timedelta(seconds=report_interval)
  epsilon = datetime.timedelta(seconds=epsilon)
  return abs(report_interval - tdelta) <= epsilon


def parse_log_line(line):
  """Parses data from a DEBUG log line."""

  m = REPORT_STATE_RE.match(line)
  if not m:
    return None, None, None

  log_data = eval(m.group(2))
  ts = datetime.datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S')
  binary = log_data['args']['agent_state']['agent_state']['binary']
  vhost = log_data['args']['agent_state']['agent_state']['host']
  return ts, binary, vhost


def main():
  ts_vhosts = {}
  bad_ts_vhosts = collections.defaultdict(list)

  for line in sys.stdin.readlines():
    ts, binary, vhost = parse_log_line(line)
    if not ts:
      continue
    if binary != NEUTRON_BINARY:
      continue
    if vhost in ts_vhosts:
      if not is_report_interval(ts_vhosts[vhost], ts):
        bad_ts_vhosts[vhost].append((ts_vhosts[vhost], ts))
    ts_vhosts[vhost] = ts

  for vhost, bad_tss in bad_ts_vhosts.iteritems():
    for ts1, ts2 in bad_tss:
      print '! %-20s (%s, %s) (%s)' % (vhost, ts1, ts2, ts2-ts1)


if __name__ == "__main__":
    sys.exit(main())
