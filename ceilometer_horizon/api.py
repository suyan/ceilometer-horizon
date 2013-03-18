# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import urlparse

from django.conf import settings
from ceilometerclient import client as ceilometer_client

from horizon import exceptions

from .base import APIResourceWrapper, APIDictWrapper, url_for

import keystone

LOG = logging.getLogger(__name__)


class Meter(APIResourceWrapper):
    _attrs = ['name', 'type', 'unit', 'resource_id', 'user_id',
              'project_id']


class Resource(APIResourceWrapper):
    _attrs = ['resource_id', "source", "user_id", "project_id"]


class Sample(APIResourceWrapper):
    _attrs = ['counter_name', 'user_id', 'resource_id', 'timestamp',
              'resource_metadata', 'source', 'counter_unit', 'counter_volume',
              'project_id', 'counter_type', 'resource_metadata']

    @property
    def instance(self):
        if 'display_name' in self.resource_metadata:
            return self.resource_metadata['display_name']
        elif 'instance_id' in self.resource_metadata:
            return self.resource_metadata['instance_id']
        else:
            return None


class GlobalDiskUsage(APIDictWrapper):
    _attrs = ["tenant", "user", "resource", "disk_read_bytes",
              "disk_read_requests", "disk_write_bytes",
              "disk_write_requests"]


class GlobalNetworkUsage(APIResourceWrapper):
    _attrs = ["tenant", "user", "resource", "network_incoming_bytes",
              "network_incoming_packets", "network_outgoing_bytes",
              "network_outgoing_packets"]


class Statistic(APIResourceWrapper):
    _attrs = ['period', 'period_start', 'period_end',
              'count', 'min', 'max', 'sum', 'avg',
              'duration', 'duration_start', 'duration_end']


def ceilometerclient(request):
    o = urlparse.urlparse(url_for(request, 'metering'))
    url = "://".join((o.scheme, o.netloc))
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    LOG.debug('ceilometerclient connection created using token "%s" '
              'and url "%s"' % (request.user.token.id, url))
    return ceilometer_client.Client('2', url, token=request.user.token.id,
                             insecure=insecure)


def sample_list(request, meter_name, query=[]):
    """List the samples for this meters."""
    try:
        samples = ceilometerclient(request).\
            samples.list(meter_name=meter_name,
                         q=query)
    except:
        samples = []
        LOG.exception("Sample list from Ceilometer not found: %s" % meter_name)
        exceptions.handle(request)

    return [Sample(s) for s in samples]


def meter_list(request, query=[]):
    """List the user's meters."""
    meters = ceilometerclient(request).meters.list(q=query)
    return meters


def resource_list(request, query=[]):
    """List the resources."""
    resources = ceilometerclient(request).\
        resources.list(query)
    return resources


def statistic_get(request, meter_name, query=[]):
    statistics = ceilometerclient(request).\
        statistics.list(meter_name=meter_name, q=query)
    assert len(statistics) == 1
    return Statistic(statistics[0])


def global_disk_usage(request):
    return global_usage(request, ["disk.read.bytes", "disk.read.requests",
                             "disk.write.bytes", "disk.write.requests"])


def global_network_usage(request):
    return global_usage(request, ["network.incoming.bytes",
                                  "network.incoming.packets",
                                  "network.outgoing.bytes",
                                  "network.outgoing.packets"])


def global_usage(request, fields):
    meters = meter_list(request)

    filtered = filter(lambda m: m.name in fields, meters)

    def get_query(user, project, resource):
        query = [({"field": "resource", "op": "eq", "value": resource}),
                 ({"field": "user", "op": "eq", "value": user}),
                 ({"field": "project", "op": "eq", "value": project})
        ]
        return query

    usage_list = []
    ks_user_list = keystone.user_list(request)
    ks_tenant_list = keystone.tenant_list(request, admin=True)

    def get_user(user_id):
        for u in ks_user_list:
            if u.id == user_id:
                return u.name
        return user_id

    def get_tenant(tenant_id):
        for t in ks_tenant_list:
            if t.id == tenant_id:
                return t.name
        return tenant_id

    for m in filtered:
        statistic = statistic_get(request, m.name,
            query=get_query(m.user_id, m.project_id, m.resource_id))
        usage_list.append({"tenant": get_tenant(m.project_id),
                      "user": get_user(m.user_id),
                      "total": statistic.max,
                      "counter_name": m.name.replace(".", "_"),
                      "resource": m.resource_id})
    return [GlobalDiskUsage(u) for u in _group_usage(usage_list)]


def _group_usage(usage_list):
    """
    Group usage data of different counters to one object.
    The usage data in one group have the same resource,
    user and project.
    """
    result = {}
    for s in usage_list:
        key = "%s_%s_%s" % (s['user'], s['tenant'], s['resource'])
        if key not in result:
            result[key] = s
        result[key].setdefault(s['counter_name'], s['total'])
    return result.values()
