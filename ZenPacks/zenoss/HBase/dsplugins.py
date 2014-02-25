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
log = getLogger('zen.python')

import re
import time
import json
from twisted.web.client import getPage
from twisted.internet import defer

from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource \
    import PythonDataSourcePlugin
from Products.DataCollector.plugins.DataMaps import ObjectMap

from Products.ZenEvents import ZenEventClasses
from Products.ZenUtils.Utils import prepId
from ZenPacks.zenoss.HBase import MODULE_NAME, NAME_SPLITTER
from ZenPacks.zenoss.HBase.utils import hbase_rest_url

import ZenPacks.zenoss.HBase.modeler.plugins.HBaseCollector as HBaseCollector

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
        'zHBasePasword',
        'zHBasePort'
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
        '''
        Create Object/Relationship map for component remodeling.

        @param res: dict with key enum_info and value Item object
        @type res: dict
        @param datasource: device datasourse
        @type datasource: instance of PythonDataSourceConfig
        @return: ObjectMap|RelationshipMap
        '''
        return []

    def get_events(self, result):
        """
        Return evants for the component.
        """
        return []

    @defer.inlineCallbacks
    def collect(self, config):
        """
        This method return a Twisted deferred. The deferred results will
        be sent to the onResult then either onSuccess or onError callbacks
        below.
        """
        results = self.new_data()
        for ds in config.datasources:
            if ds.zHBase == "false":
                continue

            # print "==" * 20
            # print ds.component
            self.component = ds.component

            url = hbase_rest_url(
                user=ds.zHBaseUsername,
                passwd=ds.zHBasePasword,
                port=ds.zHBasePort,
                host=ds.manageIp,
                endpoint=self.endpoint
            )

            try:
                res = yield getPage(
                    url, headers={'Accept': 'application/json'}
                )
                if not res:
                    raise HBaseException('No monitoring data.')
                results['values'][self.component] = self.process(res)
                results['events'].extend(self.get_events(res))

                maps = self.add_maps(res, ds)

                if maps:
                    results['maps'].extend(maps)
            except (Exception, HBaseException), e:
                print e
                results['events'].append({
                    'component': ds.component,
                    'summary': str(e),
                    'eventKey': 'hbase_monitoring_error',
                    'eventClass': '/Status',
                    'severity': ZenEventClasses.Critical,
                })
        defer.returnValue(results)

    def onSuccess(self, result, config):
        """
        This method return a data structure with zero or more events, values
        and maps.  result - is what returned from collect.
        """
        results = {
            'values': result['values'],
            'events': result['events'],
            'maps': result['maps'],
        }
        for component in result['values'].keys():
            results['events'].insert(0, {
                'component': component,
                'summary': 'Monitoring ok',
                'eventKey': 'hbase_monitoring_error',
                'eventClass': '/Status',
                'severity': ZenEventClasses.Clear,
            })
        return results

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

    def get_events(self, result):
        data = json.loads(result)
        summary = ''
        # Check if server exists.
        live_nodes = [prepId(node['name']) for node in data["LiveNodes"]]
        if self.component not in live_nodes:
            summary = 'This region server does not exist.'
        # Check if server is dead.
        if self.component in [prepId(node) for node in data["DeadNodes"]]:
            summary = 'This region server is dead.'
        if summary:
            return [{
                'component': self.component,
                'summary': summary,
                'eventKey': 'hbase_monitoring_error',
                'eventClass': '/Status',
                'severity': ZenEventClasses.Error,
            }]
        return []

    def add_maps(self, result, ds):
        """
        Parses resulting data into datapoints
        """
        ds.id = ds.component
        return HBaseCollector.HBaseCollector().process(ds, result, log)


class HBaseRegionPlugin(HBaseBasePlugin):
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

    def get_events(self, result):
        data = json.loads(result)
        node_id, region_id = self.component.split(NAME_SPLITTER)
        regions = [prepId(region['name']) for node in data["LiveNodes"]
            for region in node["Region"]]
        if region_id not in regions:
            return [{
                'component': self.component,
                'summary': 'This region does not exist.',
                'eventKey': 'hbase_monitoring_error',
                'eventClass': '/Status',
                'severity': ZenEventClasses.Error,
            }]
        return []


def _sum_perf_metrics(res, region):
    """
    Util function for summing region metrics
    """
    res['read_requests'] = (res['read_requests'][0] + \
        region['readRequestsCount'], 'N')
    res['write_requests'] = (res['write_requests'][0] + \
        region['writeRequestsCount'], 'N')
    res['number_of_stores'] = (res['number_of_stores'][0] + \
        region['stores'], 'N')
    res['number_of_store_files'] = (res['number_of_store_files'][0] + \
        region['storefiles'], 'N')
    res['store_file_size_mb'] = (res['store_file_size_mb'][0] + \
        region['storefileSizeMB'], 'N')
    res['store_file_index_size_mb'] = (res['store_file_index_size_mb'][0] + \
        region['storefileIndexSizeMB'], 'N')
    res['memstore_size_mb'] = (res['memstore_size_mb'][0] + \
        region['memstoreSizeMB'], 'N')
    res['current_compacted_kv'] = (res['current_compacted_kv'][0] + \
        region['currentCompactedKVs'], 'N')
    res['total_compacting_kv'] = (res['total_compacting_kv'][0] + \
        region['totalCompactingKVs'], 'N')
    return res
