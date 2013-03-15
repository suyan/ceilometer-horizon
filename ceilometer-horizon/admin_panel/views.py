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
import csv
from datetime import datetime, timedelta

from horizon import tabs, views
from django.http import HttpResponse
from django.views.generic import View

from .tabs import CeilometerOverviewTabs
from openstack_dashboard.api import ceilometer


LOG = logging.getLogger(__name__)


class IndexView(tabs.TabbedTableView):
    tab_group_class = CeilometerOverviewTabs
    template_name = 'admin/ceilometer/index.html'


class SamplesView(View):

    # converts string to date
    def _to_iso_time(self, date_str):
        date_object = datetime.strptime(date_str, '%m/%d/%Y %H:%M:%S')
        return date_object.isoformat(' ')

    # grab the latest sample value before that date
    def _get_previous_val(self, source, resource, limit_date):
        # give 1 hour of margin to grab latest sample
        date_object = datetime.strptime(limit_date, '%Y-%m-%d %H:%M:%S')
        edge_date = date_object - timedelta(hours=1)
        edge_date_str = edge_date.strftime('%Y-%m-%d %H:%M:%S')

        query = [
            {'field':'timestamp', 'op':'ge', 'value':edge_date_str},
            {'field':'timestamp', 'op':'lt', 'value':limit_date},
            {'field':'resource', 'op':'eq', 'value':resource}
        ]
        sample_list = ceilometer.sample_list(self.request, source, query)
        if len(sample_list)>0:
            # grab latest item
            last = sample_list[-1]
            print last.timestamp
            print last.counter_volume
            return last.counter_volume
        else:
            return 0

    def get(self, request, *args, **kwargs):
        source = request.GET.get('sample', '')
        date_from = request.GET.get('from', '')
        date_to = request.GET.get('to', '')
        resource = request.GET.get('resource', '')
        query = []
        rows = []

        if date_from:
            date_from = self._to_iso_time(date_from+' 00:00:00')
            query.append({'field':'timestamp', 'op':'ge', 'value':date_from})

        if date_to:
            date_to = self._to_iso_time(date_to+" 23:59:59")
            query.append({'field':'timestamp', 'op':'le', 'value':date_to})

        if source and resource:
            query.append({'field':'resource', 'op':'eq', 'value':resource})
            sample_list = ceilometer.sample_list(self.request, source, query)

            samples = []
            previous = self._get_previous_val(source, resource, date_from)

            for sample_data in sample_list:
                current_delta = sample_data.counter_volume - previous
                previous = sample_data.counter_volume
                if current_delta<0:
                    current_delta = 0
                samples.append([sample_data.timestamp, current_delta])

        # output csv
        headers = ['date', 'value']
        response = HttpResponse(mimetype='text/csv')
        writer = csv.writer(response)
        writer.writerow(headers)

        for sample in samples:
            writer.writerow(sample)

        return response
