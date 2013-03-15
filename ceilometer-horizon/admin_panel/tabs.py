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

from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard.api import ceilometer

from .tables import DiskUsageTable, NetworkUsageTable


class DiskUsageTab(tabs.TableTab):
    table_classes = (DiskUsageTable,)
    name = _("Global Disk Usage")
    slug = "global_disk_usage"
    template_name = ("horizon/common/_detail_table.html")

    def get_global_disk_usage_data(self):
        request = self.tab_group.request
        result = sorted(api.ceilometer.global_disk_usage(request), key=operator.itemgetter('tenant', 'user'))
        return result


class NetworkUsageTab(tabs.TableTab):
    table_classes = (NetworkUsageTable,)
    name = _("Global Network Usage")
    slug = "global_network_usage"
    template_name = ("horizon/common/_detail_table.html")

    def get_global_network_usage_data(self):
        request = self.tab_group.request
        result = sorted(api.ceilometer.global_network_usage(request), key=operator.itemgetter('tenant', 'user'))
        return result

class StatsTab(tabs.Tab):
    name = _("Stats")
    slug = "stats"
    template_name = ("admin/ceilometer/stats.html")

    def get_context_data(self, request):
        context = {}
        meter_list = ceilometer.meter_list(self.request)
        resource_list = ceilometer.resource_list(self.request)

        meters = []
        # we will allow charts of cumulative type
        for meter in meter_list:
            if meter.type == "cumulative":
                if meter.name not in meters:
                    meters.append(meter.name)

        # list all resources, grouped by tenant/user
        resources = {}
        for resource in resource_list:
            if resource.project_id not in resources:
                resources[resource.project_id] = {}

            if resource.user_id not in resources[resource.project_id]:
                resources[resource.project_id][resource.user_id] = []

            resources[resource.project_id][resource.user_id].append(resource.resource_id)

        context = {'meters': meters, 'resources': resources}
        return context

class CeilometerOverviewTabs(tabs.TabGroup):
    slug = "ceilometer_overview"
    tabs = (DiskUsageTab, NetworkUsageTab,StatsTab,)
    sticky = True
