######################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is
# installed.
#
######################################################################

from logging import getLogger
log = getLogger('zen.zenpython')

import re
import json

from twisted.web.client import getPage
from twisted.internet import defer

from Products.DataCollector.plugins.DataMaps import ObjectMap
from Products.ZenEvents import ZenEventClasses
from Products.ZenUtils.Utils import prepId
from ZenPacks.zenoss.HBase import MODULE_NAME, NAME_SPLITTER
from ZenPacks.zenoss.HBase.utils import hbase_rest_url, hbase_headers, dead_node_name
from ZenPacks.zenoss.HBase.modeler.plugins.HBaseCollector import HBaseCollector
from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource \
    import PythonDataSourcePlugin


class HBaseException(Exception):
    pass


class HBaseBasePlugin(PythonDataSourcePlugin):
    """
    Datasource for HBase Device
    and base for components' datasource classes.
    """

    proxy_attributes = (
        'zHBase',
        'zHBaseUsername',
        'zHBasePassword',
        'zHBasePort',
        'regionserver_ids'
    )

    component = None

    endpoint = '/status/cluster'

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
        Create Object/Relationship map for component remodeling.

        @param res: the data returned from getPage call
        @type res: str
        @param datasource: device datasourse
        @type datasource: instance of PythonDataSourceConfig
        @return: ObjectMap|RelationshipMap
        """
        # The function must run only once, as it remodels all region servers.
        ds.id = ds.device
        return HBaseCollector().process(ds, res, log)

    def get_events(self, result, ds):
        """
        Form events for a particular component.

        @param result: the data returned from getPage call
        @type result: str
        @param ds: device datasourse
        @type ds: instance of PythonDataSourceConfig
        @return: list of events
        """
        data = json.loads(result)
        events = []
        # Check for removed/added servers.
        dead_nodes = [prepId(dead_node_name(node)[0]) for node
                      in data["DeadNodes"]]
        live_nodes = [prepId(node['name']) for node in data["LiveNodes"]]
        all_nodes = dead_nodes + live_nodes

        added = list(set(all_nodes).difference(set(ds.regionserver_ids)))
        removed = list(set(ds.regionserver_ids).difference(set(all_nodes)))
        for server in added:
            events.append({
                'component': server,
                'summary': "Region server '{0}' is added.".format(
                    server.replace('_', ':')),
                'eventClass': '/Status',
                'severity': ZenEventClasses.Info,
            })
        for server in removed:
            events.append({
                'summary': "Region server '{0}' is removed.".format(
                    server.replace('_', ':')),
                'eventClass': '/Status',
                'severity': ZenEventClasses.Info,
            })
        return events

    @defer.inlineCallbacks
    def collect(self, config):
        """
        This method return a Twisted deferred. The deferred results will
        be sent to the onResult then either onSuccess or onError callbacks
        below.
        """
        results = self.new_data()
        res = ''

        ds0 = config.datasources[0]
        if not ds0.zHBase:
            defer.returnValue(results)
        # Check the connection and collect data.
        url = hbase_rest_url(
            port=ds0.zHBasePort,
            host=ds0.manageIp,
            endpoint=self.endpoint
        )
        headers = hbase_headers(
            accept='application/json',
            username=ds0.zHBaseUsername,
            passwd=ds0.zHBasePassword
        )
        try:
            res = yield getPage(url, headers=headers)
            if not res:
                raise HBaseException('No monitoring data.')
        except (Exception, HBaseException), e:
            # Send connection error event for each component.
            for ds in config.datasources:
                results['events'].append({
                    'component': ds.component,
                    'summary': str(e),
                    'eventKey': 'hbase_monitoring_error',
                    'eventClass': '/Status',
                    'severity': ZenEventClasses.Critical,
                })
            defer.returnValue(results)
        # Process returned data.
        for ds in config.datasources:
            self.component = ds.component
            results['values'][self.component] = self.process(res)
            maps = self.add_maps(res, ds)
            if maps:
                results['maps'].extend(maps)
            results['events'].extend(self.get_events(res, ds))
        defer.returnValue(results)

    def onSuccess(self, result, config):
        """
        This method return a data structure with zero or more events, values
        and maps.  result - is what returned from collect.
        """
        for component in result['values'].keys():
            result['events'].append({
                'component': component,
                'summary': 'Monitoring ok',
                'eventKey': 'hbase_monitoring_error',
                'eventClass': '/Status',
                'severity': ZenEventClasses.Clear,
            })
        return result

    def onError(self, result, config):
        data = self.new_data()
        data['events'].append({
            'component': self.component,
            'summary': str(result),
            'eventKey': 'hbase_monitoring_error',
            'eventClass': '/Status',
            'severity': ZenEventClasses.Error,
        })
        return data


class HBaseRegionServerPlugin(HBaseBasePlugin):
    """
    Datasource for HBase Region Server component.
    """

    def process(self, result):
        """
        Parses resulting data into datapoints
        """
        data = json.loads(result)

        for node in data["LiveNodes"]:
            if self.component == prepId(node['name']):
                res = {
                    'requests_per_second': (node['requests'], 'N'),
                    'used_heap_mb': (node['heapSizeMB'], 'N'),
                    'max_heap_mb': (node['maxHeapSizeMB'], 'N'),
                    'regions': (len(node['Region']), 'N'),
                    'read_requests': (0, 'N'),
                    'write_requests': (0, 'N'),
                    'number_of_stores': (0, 'N'),
                    'number_of_store_files': (0, 'N'),
                    'store_file_size_mb': (0, 'N'),
                    'store_file_index_size_mb': (0, 'N'),
                    'memstore_size_mb': (0, 'N'),
                    'current_compacted_kv': (0, 'N'),
                    'total_compacting_kv': (0, 'N'),
                }
                for region in node["Region"]:
                    res = _sum_perf_metrics(res, region)
                return res
        return {}

    def get_events(self, result, ds):
        data = json.loads(result)
        # Check for dead servers.
        dead_nodes = [prepId(dead_node_name(node)[0]) for node
                      in data["DeadNodes"]]
        # Send error or clear event.
        severity = ((self.component in dead_nodes) and ZenEventClasses.Error
                    or ZenEventClasses.Clear)
        return [{
            'component': self.component,
            'summary': "Region server '{0}' is dead.".format(
                self.component.replace('_', ':')),
            'eventKey': 'hbase_regionserver_monitoring_error',
            'eventClass': '/Status',
            'severity': severity
        }]

    def add_maps(self, res, ds):
        return []


class HBaseHRegionPlugin(HBaseBasePlugin):
    """
    Datasource for HBase Region component.
    """

    def process(self, result):
        """
        Parses resulting data into datapoints
        """
        data = json.loads(result)
        node_id, region_id = self.component.split(NAME_SPLITTER)
        res = {}

        for node in data["LiveNodes"]:
            if node_id == prepId(node['name']):
                for region in node["Region"]:
                    if region_id == prepId(region['name']):
                        res = {
                            'read_requests': (0, 'N'),
                            'write_requests': (0, 'N'),
                            'number_of_stores': (0, 'N'),
                            'number_of_store_files': (0, 'N'),
                            'store_file_size_mb': (0, 'N'),
                            'store_file_index_size_mb': (0, 'N'),
                            'memstore_size_mb': (0, 'N'),
                            'current_compacted_kv': (0, 'N'),
                            'total_compacting_kv': (0, 'N'),
                        }
                        return _sum_perf_metrics(res, region)
        return res

    def add_maps(self, res, ds):
        return []

    def get_events(self, result, ds):
        return []


class HBaseTablePlugin(HBaseBasePlugin):
    """
    Datasource for HBase Table component.
    """
    endpoint = '/table.jsp?name={0}'

    @defer.inlineCallbacks
    def collect(self, config):
        """
        This method overrides the HBaseBasePlugin.collect method.
        """
        results = self.new_data()
        for ds in config.datasources:
            if not ds.zHBase:
                continue

            self.component = ds.component
            url = hbase_rest_url(
                port='60010',
                host=ds.manageIp,
                endpoint=self.endpoint.format(self.component)
            )
            headers = hbase_headers(
                accept='text/html',
                username=ds.zHBaseUsername,
                passwd=ds.zHBasePassword
            )
            try:
                # Check connection and collect data.
                res = yield getPage(url, headers=headers)
                if not res:
                    raise HBaseException('No monitoring data.')
                # Process data if was returned.
                results['maps'].extend(self.add_maps(res, ds))
                results['events'].extend(self.get_events(res, ds))
            except (Exception, HBaseException), e:
                summary = str(e)
                if '500' in summary:
                    summary = "The table '{0}' is broken or does not " \
                        "exist.".format(ds.component)
                results['events'].append({
                    'component': ds.component,
                    'summary': summary,
                    'eventKey': 'hbase_monitoring_error',
                    'eventClass': '/Status',
                    'severity': ZenEventClasses.Critical,
                })
        defer.returnValue(results)

    def onSuccess(self, result, config):
        # Clear events for those components, who have maps.
        clear_components = [om.compname.replace('hbase_tables/', '')
                            for om in result['maps']]
        for component in clear_components:
            result['events'].append({
                'component': component,
                'summary': 'Monitoring ok',
                'eventKey': 'hbase_monitoring_error',
                'eventClass': '/Status',
                'severity': ZenEventClasses.Clear,
            })
        return result

    def add_maps(self, result, ds):
        return [ObjectMap({
            "compname": "hbase_tables/%s" % self.component,
            "modname": "HBase table state",
            "enabled": _table_enabled(result),
            "compaction": _table_compaction(result)
        })]

    def get_events(self, result, ds):
        enabled = _table_enabled(result)
        summary = 'Monitoring ok'
        if enabled != 'true':
            summary = "The table '{0}' is disabled.".format(self.component)
        if not enabled:
            summary = "The table '{0}' is dropped.".format(self.component)
        # Send error or clear event.
        severity = ((summary != 'Monitoring ok') and ZenEventClasses.Error
                    or ZenEventClasses.Clear)
        return [{
            'component': self.component,
            'summary': summary,
            'eventKey': 'hbase_table_monitoring_error',
            'eventClass': '/Status',
            'severity': severity,
        }]


def _sum_perf_metrics(res, region):
    """
    Util function for summing region metrics
    """
    res['read_requests'] = (res['read_requests'][0] +
                            region['readRequestsCount'], 'N')
    res['write_requests'] = (res['write_requests'][0] +
                             region['writeRequestsCount'], 'N')
    res['number_of_stores'] = (res['number_of_stores'][0] +
                               region['stores'], 'N')
    res['number_of_store_files'] = (res['number_of_store_files'][0] +
                                    region['storefiles'], 'N')
    res['store_file_size_mb'] = (res['store_file_size_mb'][0] +
                                 region['storefileSizeMB'], 'N')
    res['store_file_index_size_mb'] = (res['store_file_index_size_mb'][0] +
                                       region['storefileIndexSizeMB'], 'N')
    res['memstore_size_mb'] = (res['memstore_size_mb'][0] +
                               region['memstoreSizeMB'], 'N')
    res['current_compacted_kv'] = (res['current_compacted_kv'][0] +
                                   region['currentCompactedKVs'], 'N')
    res['total_compacting_kv'] = (res['total_compacting_kv'][0] +
                                  region['totalCompactingKVs'], 'N')
    return res


def _table_enabled(res):
    """
    Parse the getPage result for the table status.
    """
    res = res.replace('\n', '').replace(' ', '')
    matcher = re.compile(r'.+<td>Enabled</td><td>(?P<enabled>\w+)</td>')
    match = matcher.match(res)
    if match:
        return match.group('enabled')
    return ''


def _table_compaction(res):
    """
    Parse the getPage result for the table compaction.
    """
    res = res.replace('\n', '').replace(' ', '')
    matcher = re.compile(r'.+<td>Compaction</td><td>(?P<compaction>\w+)</td>')
    match = matcher.match(res)
    if match:
        return match.group('compaction')
    return ''
