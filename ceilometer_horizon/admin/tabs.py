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

from openstack_dashboard import api
from ..api import ceilometer
from openstack_dashboard.api import keystone

from .tables import DiskUsageTable, NetworkUsageTable


class DiskUsageTab(tabs.TableTab):
    table_classes = (DiskUsageTable,)
    name = _("Global Disk Usage")
    slug = "global_disk_usage"
    template_name = ("horizon/common/_detail_table.html")

    def get_global_disk_usage_data(self):
        request = self.tab_group.request
        result = sorted(ceilometer.global_disk_usage(request), key=operator.itemgetter('tenant', 'user'))
        return result


class NetworkUsageTab(tabs.TableTab):
    table_classes = (NetworkUsageTable,)
    name = _("Global Network Usage")
    slug = "global_network_usage"
    template_name = ("horizon/common/_detail_table.html")

    def get_global_network_usage_data(self):
        request = self.tab_group.request
        result = sorted(ceilometer.global_network_usage(request), key=operator.itemgetter('tenant', 'user'))
        return result

class StatsTab(tabs.Tab):
    name = _("Stats")
    slug = "stats"
    template_name = ("admin/ceilometer/stats.html")

    def get_context_data(self, request):
        context = {}
        meter_list = ceilometer.meter_list(self.request)

        meters = []
        found_meters = []
        # we will allow charts of cumulative type
        for meter in meter_list:
            if meter.type == "cumulative":
                if meter.name not in found_meters:
                    if "network" in meter.name:
                        meter_type = "network"
                    else:
                        meter_type = "instance"
                    meters.append({"name":meter.name, "type":meter_type})
                    found_meters.append(meter.name)

        # first list all tenants
        resources = {}
        users = keystone.user_list(request)

        for user in users:
            if user.id not in resources:
                user_data = {}
                user_data["id"] = user.id
                user_data["name"] = user.name
                user_data["resources"] = []
                resources[user.id] = user_data

            # read resources for that user
            query = [
                {'field':'user', 'op':'eq', 'value':user.id}
            ]

            resource_list = ceilometer.resource_list(self.request, query)
            for resource in resource_list:
                if resource.resource_id not in resources[user.id]["resources"]:
                    if "mac" in resource.metadata:
                        resource_type = "network"
                    else:
                        resource_type = "instance"

                    resources[user.id]["resources"].append({"id":resource.resource_id, "name":resource.metadata["name"]+" - "+resource.resource_id, "type":resource_type})

            # sort by resource name
            resources[user.id]["resources"] = sorted(resources[user.id]["resources"], key=operator.itemgetter("name"))

        resources = sorted(resources.values(), key=operator.itemgetter("name"))
        context = {'meters': meters, 'resources': resources}
        context.update(csrf(request))
        return context

class CeilometerOverviewTabs(tabs.TabGroup):
    slug = "ceilometer_overview"
    tabs = (DiskUsageTab, NetworkUsageTab,StatsTab,)
    sticky = True
