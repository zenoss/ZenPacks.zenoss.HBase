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

from Products.ZenUtils.Utils import prepId
from ZenPacks.zenoss.HBase import NAME_SPLITTER
from ZenPacks.zenoss.HBase.dsplugins.base_plugin import HBaseBasePlugin, sum_perf_metrics
from ZenPacks.zenoss.HBase.utils import version_diff

log = getLogger('zen.HBasePlugins')


class HBaseHRegionPlugin(HBaseBasePlugin):
    """
    Datasource plugin for HBase Region component.
    """

    eventKey = 'hbase_region_monitoring_error'

    def process(self, result):
        """
        Parses resulting data into datapoints.
        """
        data = json.loads(result)
        node_id, region_id = self.component.split(NAME_SPLITTER)
        res = {}

        for node in version_diff(data["LiveNodes"]):
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
                        return sum_perf_metrics(res, region)
        return res
