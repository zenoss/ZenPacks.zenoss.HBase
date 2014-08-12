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

from twisted.web.client import getPage
from twisted.internet import defer

from Products.DataCollector.plugins.DataMaps import ObjectMap, RelationshipMap
from Products.ZenEvents import ZenEventClasses
from Products.ZenUtils.Utils import convToUnits
from ZenPacks.zenoss.HBase.dsplugins.base_plugin import HBaseBasePlugin
from ZenPacks.zenoss.HBase.utils import (
    hbase_rest_url, hbase_headers, matcher, HBaseException
)

log = getLogger('zen.HBasePlugins')


class HBaseTablePlugin(HBaseBasePlugin):
    """
    Datasource plugin for HBase Table component.
    """
    endpoint = '/table.jsp?name={0}'

    proxy_attributes = HBaseBasePlugin.proxy_attributes + ('zHBaseMasterPort',)

    @defer.inlineCallbacks
    def collect(self, config):
        """
        This method overrides the HBaseBasePlugin.collect method.
        """
        results = self.new_data()
        for ds in config.datasources:
            self.component = ds.component
            headers = hbase_headers(
                accept='application/json',
                username=ds.zHBaseUsername,
                passwd=ds.zHBasePassword
            )
            # Get compaction and state of the table.
            url = hbase_rest_url(
                scheme=ds.zHBaseScheme,
                port=ds.zHBaseMasterPort,
                host=ds.manageIp,
                endpoint=self.endpoint.format(self.component)
            )
            # Get column family information.
            schema_url = hbase_rest_url(
                scheme=ds.zHBaseScheme,
                port=ds.zHBaseRestPort,
                host=ds.manageIp,
                endpoint='/{}/schema'.format(self.component)
            )
            try:
                # Check connection and collect data.
                res = yield getPage(url, headers=headers)
                schema = yield getPage(schema_url, headers=headers)
                if not res:
                    raise HBaseException('No monitoring data.')
                # Process data if was returned.
                results['maps'].extend(self.add_maps(res, schema, ds))
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
        """
        Return data structure with events, values and maps.
        """
        # Clear events for those components, which have maps.
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

    def add_maps(self, result, schema, ds):
        """
        Return a list of ObjectMaps with properties updates for each table.
        """
        schema = json.loads(schema)
        return [ObjectMap({
            "compname": "hbase_tables/%s" % self.component,
            "modname": "HBase table state",
            "enabled": matcher(result, r'.+<td>Enabled</td><td>(\w+)</td>'),
            "compaction": matcher(result, r'.+<td>Compaction</td><td>(\w+)</td>'),
            "number_of_col_families": len(schema.get('ColumnSchema')),
            "col_family_block_size": _block_size(schema.get('ColumnSchema')),
        })]

    def get_events(self, result, ds):
        """
        Return a list of event dictionaries informing about the health
        of the table.
        """
        enabled = matcher(result, r'.+<td>Enabled</td><td>(\w+)</td>')
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


def _block_size(column_families):
    """
    Return the value for column family block size property.

    @param column_families: list of table's column families
    @type column_families: list
    @return: string value
    """
    result = [
        '{}: {}; '.format(
            family.get('name'), convToUnits(family.get('BLOCKSIZE'))
        ) for family in column_families
    ]
    return ''.join(result).rstrip("; ")
