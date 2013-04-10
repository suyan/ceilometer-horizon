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
import operator

from django.utils.translation import ugettext_lazy as _
from django.core.context_processors import csrf

from horizon import tabs

from ..api import ceilometer

from .tables import (DiskUsageTable, NetworkTrafficUsageTable,
                     CpuUsageTable, ObjectStoreUsageTable, NetworkUsageTable)


class DiskUsageTab(tabs.TableTab):
    table_classes = (DiskUsageTable,)
    name = _("Global Disk Usage")
    slug = "global_disk_usage"
    template_name = ("horizon/common/_detail_table.html")

    def get_global_disk_usage_data(self):
        request = self.tab_group.request
        result = sorted(ceilometer.global_disk_usage(request),
                        key=operator.itemgetter('tenant', 'user'))
        return result


class NetworkTrafficUsageTab(tabs.TableTab):
    table_classes = (NetworkTrafficUsageTable,)
    name = _("Global Network Traffic Usage")
    slug = "global_network_traffic_usage"
    template_name = ("horizon/common/_detail_table.html")

    def get_global_network_traffic_usage_data(self):
        request = self.tab_group.request
        result = sorted(ceilometer.global_network_traffic_usage(request),
                        key=operator.itemgetter('tenant', 'user'))
        return result


class NetworkUsageTab(tabs.TableTab):
    table_classes = (NetworkUsageTable,)
    name = _("Global Network Usage")
    slug = "global_network_usage"
    template_name = ("horizon/common/_detail_table.html")

    def get_global_network_usage_data(self):
        request = self.tab_group.request
        result = sorted(ceilometer.global_network_usage(request),
                        key=operator.itemgetter('tenant', 'user'))
        return result


class CpuUsageTab(tabs.TableTab):
    table_classes = (CpuUsageTable,)
    name = _("Global CPU Usage")
    slug = "global_cpu_usage"
    template_name = ("horizon/common/_detail_table.html")

    def get_global_cpu_usage_data(self):
        request = self.tab_group.request
        result = sorted(ceilometer.global_cpu_usage(request),
                        key=operator.itemgetter('tenant', 'user'))
        return result


class GlobalObjectStoreUsageTab(tabs.TableTab):
    table_classes = (ObjectStoreUsageTable,)
    name = _("Global Object Store Usage")
    slug = "global_object_store_usage"
    template_name = ("horizon/common/_detail_table.html")

    def get_global_object_store_usage_data(self):
        request = self.tab_group.request
        result = sorted(ceilometer.global_object_store_usage(request),
                        key=operator.itemgetter('tenant', 'user'))
        return result


class StatsTab(tabs.Tab):
    name = _("Stats")
    slug = "stats"
    template_name = ("admin/ceilometer/stats.html")

    def get_context_data(self, request):
        context = {}
        meter_list = ceilometer.meter_list(self.request)

        meters = []
        meter_types = [
            ("Compute", [
                {"name": "cpu", "unit": "ns", "type": "cumulative"},
                {"name": "disk.read.requests", "unit": "requests",
                         "type": "cumulative"},
                {"name": "disk.read.bytes", "unit": "B",
                         "type": "cumulative"},
                {"name": "network.incoming.bytes", "unit": "B",
                         "type": "cumulative"},
                {"name": "network.outgoing.bytes", "unit": "B",
                         "type": "cumulative"},
                {"name": "network.incoming.packets", "unit": "packets",
                         "type": "cumulative"},
                {"name": "network.outgoing.packets", "unit": "packets",
                         "type": "cumulative"}]),
            ("Network", [
                {"name": "network.create", "unit": "network", "type": "delta"},
                {"name": "network.update", "unit": "network", "type": "delta"},
                {"name": "subnet.create", "unit": "subnet", "type": "delta"},
                {"name": "subnet.update", "unit": "subnet", "type": "delta"},
                {"name": "port.create", "unit": "port", "type": "delta"},
                {"name": "port.update", "unit": "port", "type": "delta"},
                {"name": "router.create", "unit": "router", "type": "delta"},
                {"name": "router.update", "unit": "router", "type": "delta"},
                {"name": "ip.floating.create", "unit": "ip", "type": "delta"},
                {"name": "ip.floating.update", "unit": "ip",
                         "type": "delta"}]),
            ("Object Storage", [
                {"name": "storage.objects.incoming.bytes", "unit": "B",
                         "type": "delta"},
                {"name": "storage.objects.outgoing.bytes", "unit": "B",
                         "type": "delta"}])
        ]

        # grab different resources for metrics,
        # and associate with the right type
        meters = ceilometer.meter_list(self.request)
        resources = {}
        for meter in meters:
            # group resources by meter names
            if meter.type=='delta' or meter.type=='cumulative':
                if meter.name not in resources:
                    resources[meter.name] = []
                if meter.resource_id not in resources[meter.name]:
                    resources[meter.name].append(meter.resource_id)

        context = {'meters': meter_types, 'resources': resources}
        context.update(csrf(request))
        return context

class CeilometerOverviewTabs(tabs.TabGroup):
    slug = "ceilometer_overview"
    tabs = (DiskUsageTab, NetworkTrafficUsageTab, NetworkUsageTab,
            GlobalObjectStoreUsageTab, CpuUsageTab, StatsTab,)
    sticky = True
