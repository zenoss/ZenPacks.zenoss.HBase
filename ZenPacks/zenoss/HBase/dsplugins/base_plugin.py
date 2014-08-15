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

from twisted.web.client import getPage
from twisted.internet import defer

from Products.ZenEvents import ZenEventClasses
from ZenPacks.zenoss.HBase.utils import (
    hbase_rest_url, hbase_headers, HBaseException, check_ssl_error
)
from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource \
    import PythonDataSourcePlugin

log = getLogger('zen.HBasePlugins')


class HBaseBasePlugin(PythonDataSourcePlugin):
    """
    Base datasource plugin for HBase Device and components'
    plugin classes.
    """

    proxy_attributes = (
        'zHBaseScheme',
        'zHBaseUsername',
        'zHBasePassword',
        'zHBaseRestPort',
    )

    component = None
    endpoint = '/status/cluster'
    # A variable to store component ids of added components.
    # Used for component remodeling and events sending.
    added = []
    # A variable to store component ids of removed components.
    removed = []

    def process(self, result):
        """
        Parses resulting data into datapoints.

        @param result: the data returned from getPage call
        @type result: str
        @return: dict of datapoints
        """
        return {}

    def add_maps(self, res, ds):
        """
        Create Object/Relationship map for component remodeling.

        @param res: the data returned from getPage call
        @type res: str
        @param datasource: device datasourse
        @type datasource: instance of PythonDataSourceConfig
        @return: ObjectMap|RelationshipMap
        """
        return []

    def get_events(self, result, ds):
        """
        Form events for a particular component.

        @param result: the data returned from getPage call
        @type result: str
        @param ds: device datasourse
        @type ds: instance of PythonDataSourceConfig
        @return: list of events
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
        res = ''

        ds0 = config.datasources[0]
        # Check the connection and collect data.
        url = hbase_rest_url(
            scheme=ds0.zHBaseScheme,
            port=ds0.zHBaseRestPort,
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
                e = check_ssl_error(e, ds.device) or e
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


# Helper functions for datasource plugins.
def sum_perf_metrics(res, region):
    """
    Util function for summing region metrics
    """
    props_match = dict(
        read_requests='readRequestsCount',
        write_requests='writeRequestsCount',
        number_of_stores='stores',
        number_of_store_files='storefiles',
        store_file_size_mb='storefileSizeMB',
        store_file_index_size_mb='storefileIndexSizeMB',
        memstore_size_mb='memstoreSizeMB',
        current_compacted_kv='currentCompactedKVs',
        total_compacting_kv='totalCompactingKVs'
    )
    for prop in props_match:
        res[prop] = (res[prop][0] + region[props_match[prop]], 'N')
    return res
