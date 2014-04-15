######################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is
# installed.
#
######################################################################

import json

from logging import getLogger

from Products.DataCollector.plugins.DataMaps import ObjectMap, RelationshipMap
from Products.ZenEvents import ZenEventClasses
from Products.ZenUtils.Utils import prepId
from ZenPacks.zenoss.HBase import MODULE_NAME
from ZenPacks.zenoss.HBase.dsplugins.base_plugin import HBaseBasePlugin, sum_perf_metrics
from ZenPacks.zenoss.HBase.modeler.plugins.HBaseCollector import HBaseCollector
from ZenPacks.zenoss.HBase.utils import dead_node_name

log = getLogger('zen.HBasePlugins')


class HBaseMasterPlugin(HBaseBasePlugin):
    """
    Datasource plugin for HBase Device (Master).
    """

    proxy_attributes = HBaseBasePlugin.proxy_attributes + (
        'regionserver_ids',
        'region_ids'
    )

    def process(self, result):
        """
        Parses resulting data into datapoints.
        """
        data = json.loads(result)

        # Calculate the percentage of dead servers.
        overall_servers = len(data['DeadNodes']) + len(data['LiveNodes'])
        percent_dead_servers = len(data['DeadNodes'])*100.00 / overall_servers

        return {
            'live_servers': (len(data['LiveNodes']), 'N'),
            'dead_servers': (len(data['DeadNodes']), 'N'),
            'requests_per_second': (data['requests'], 'N'),
            'regions': (data['regions'], 'N'),
            'average_load': (data['averageLoad'], 'N'),
            'percent_dead_servers': (percent_dead_servers, 'N'),
        }

    def add_maps(self, res, ds):
        """
        Check for added/removed regionservers and return a RelationshipMap if
        any changes took place. Otherwise return ObjectMap which only cleares
        the events of non-existiong components.
        """
        data = json.loads(res)
        # Check for removed/added region servers.
        dead_nodes = [prepId(dead_node_name(node)[0]) for node
                      in data["DeadNodes"]]
        live_nodes = [prepId(node['name']) for node in data["LiveNodes"]]
        nodes = set(dead_nodes + live_nodes)
        self.added = list(nodes.difference(set(ds.regionserver_ids)))
        self.removed = list(set(ds.regionserver_ids).difference(nodes))

        # Check for removed/added regions.
        regions = [region.get('name') for node in data["LiveNodes"]
                   for region in node.get('Region')]
        change = set(regions).symmetric_difference(ds.region_ids)
        # Remodel Regions and RegionServers only if some of them
        # were added/removed.
        if self.added or self.removed or change:
            ds.id = ds.device
            result = {'status': res, 'conf': None}
            return HBaseCollector().process(ds, result, log)
        # If nothing changed, just clear events.
        return [ObjectMap({'getClearEvents': True})]

    def get_events(self, result, ds):
        """
        Return a list of event dictionaries informing about adding or
        removing a region server.
        """
        # No need to create events on first remodel.
        if not ds.regionserver_ids:
            return []
        events = []
        for server in self.added:
            events.append({
                'component': server,
                'summary': "Region server '{0}' is added.".format(
                    server.replace('_', ':')),
                'eventClass': '/Status',
                'severity': ZenEventClasses.Info,
            })
        for server in self.removed:
            events.append({
                'summary': "Region server '{0}' is removed.".format(
                    server.replace('_', ':')),
                'eventClass': '/Status',
                'severity': ZenEventClasses.Info,
            })
        return events


class HBaseMasterTablesPlugin(HBaseBasePlugin):
    """
    Datasource plugin for HBase Device (Master).
    """

    proxy_attributes = HBaseBasePlugin.proxy_attributes + (
        'table_ids',
    )
    endpoint = '/'

    def add_maps(self, res, ds):
        """
        Check for added/removed tables and return a RelationshipMap if
        any changes took place. Otherwise return empty list.
        """
        res = json.loads(res)
        if not res:
            return []
        tables_update = set(table['name'] for table in res.get('table'))
        self.added = list(tables_update.difference(set(ds.table_ids)))
        self.removed = list(set(ds.table_ids).difference(tables_update))
        if self.added or self.removed:
            tables_oms = []
            for table in tables_update:
                tables_oms.append(ObjectMap({
                    'id': prepId(table),
                    'title': table
                }))
            return [RelationshipMap(
                relname='hbase_tables',
                modname=MODULE_NAME['HBaseTable'],
                objmaps=tables_oms)]
        return []

    def get_events(self, result, ds):
        """
        Return a list of event dictionaries informing about adding or
        removing a table.
        """
        # No need to create events on first remodel.
        if not ds.table_ids:
            return []
        events = []
        for table in self.added:
            events.append({
                'component': table,
                'summary': "The table'{0}' is added.".format(table),
                'eventClass': '/Status',
                'severity': ZenEventClasses.Info,
            })
        for table in self.removed:
            events.append({
                'summary': "The table '{0}' is removed.".format(table),
                'eventClass': '/Status',
                'severity': ZenEventClasses.Info,
            })
        return events
