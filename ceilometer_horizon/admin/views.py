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
from ..api import ceilometer

from svglib.svglib import SvgRenderer
from reportlab.graphics import renderPDF
import xml.dom.minidom
import itertools
import operator

LOG = logging.getLogger(__name__)


class IndexView(tabs.TabbedTableView):
    tab_group_class = CeilometerOverviewTabs
    template_name = 'admin/ceilometer/index.html'

# convert all items in list to hour level
def to_hours(item):
    date_obj = datetime.strptime(item[0], '%Y-%m-%dT%H:%M:%S')
    new_date_str = date_obj.strftime("%Y-%m-%dT%H:00:00")
    return (new_date_str, item[1])

# convert all items in list to day level
def to_days(item):
    date_obj = datetime.strptime(item[0], '%Y-%m-%dT%H:%M:%S')
    new_date_str = date_obj.strftime("%Y-%m-%dT00:00:00")
    return (new_date_str, item[1])

# given a set of metrics with same key, group them and calc average
def reduce_metrics(samples):
    new_samples = []
    for key, items in itertools.groupby(samples, operator.itemgetter(0)):
        grouped_items = []
        for item in items:
            grouped_items.append(item[1])
        item_len = len(grouped_items)
        if item_len>0:
            avg = reduce(lambda x, y: x+y, grouped_items)/item_len
        else:
            avg = 0

        new_samples.append([key, avg])
    return new_samples

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

        samples = []
        meter_type = ""
        if source and resource:
            query.append({'field':'resource', 'op':'eq', 'value':resource})
            sample_list = ceilometer.sample_list(self.request, source, query)

            previous = self._get_previous_val(source, resource, date_from)

            for sample_data in sample_list:
                current_volume = sample_data.counter_volume

                # if sample is cumulative, substract previous val
                meter_type = sample_data.counter_type
                if sample_data.counter_type=="cumulative":
                    current_delta = current_volume - previous
                    previous = current_volume
                    if current_delta<0:
                        current_delta = current_volume
                else:
                    current_delta = current_volume
                samples.append([sample_data.timestamp[:19], current_delta])

            # if requested period is too long, interpolate data, for cumulative metrics
            if meter_type=="cumulative":
                date_start_obj = datetime.strptime(date_from, "%Y-%m-%d %H:%M:%S")
                date_end_obj = datetime.strptime(date_to, "%Y-%m-%d %H:%M:%S")
                delta = (date_end_obj - date_start_obj).days

                if delta>=365:
                    samples = map(to_days, samples)
                    samples = reduce_metrics(samples)
                elif delta>=30:
                    # reduce metrics to hours
                    samples = map(to_hours, samples)
                    samples = reduce_metrics(samples)
            else:
                # add measures of 0 for start and end 
                samples.append([date_from.replace(" ", "T"), 0])
                samples.append([date_to.replace(" ", "T"), 0])

        # output csv
        headers = ['date', 'value']
        response = HttpResponse(mimetype='text/csv')
        writer = csv.writer(response)
        writer.writerow(headers)

        for sample in samples:
            writer.writerow(sample)

        return response

class ExportView(View):
    def post(self, request, *args, **kwargs):
        data = request.POST.get('svgdata', '')

        # render svg
        doc = xml.dom.minidom.parseString(data.encode( "utf-8" ))
        svg = doc.documentElement
        svgRenderer = SvgRenderer()
        svgRenderer.render(svg)
        drawing = svgRenderer.finish()

        # output to pdf
        pdf = renderPDF.drawToString(drawing)
        response = HttpResponse(mimetype='application/pdf')
        response["Content-Disposition"]= "attachment; filename=chart.pdf"
        response.write(pdf) 

        return response
