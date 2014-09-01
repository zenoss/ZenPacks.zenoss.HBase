##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

''' Models discovery tree for HBase. '''

import collections
import json
import zope.component

from itertools import chain
from twisted.internet import defer
from twisted.web.client import getPage

from Products.DataCollector.plugins.CollectorPlugin import PythonPlugin
from Products.DataCollector.plugins.DataMaps import ObjectMap, RelationshipMap
from Products.ZenCollector.interfaces import IEventService
from Products.ZenUtils.Utils import prepId, convToUnits
from ZenPacks.zenoss.HBase import MODULE_NAME, NAME_SPLITTER
from ZenPacks.zenoss.HBase.utils import (
    hbase_rest_url, hbase_headers, dead_node_name,
    ConfWrapper, version_diff, check_error
)


class HBaseCollector(PythonPlugin):
    '''
    PythonCollector plugin for modelling device components
    '''
    is_clear_run = True
    device_om = None

    _eventService = zope.component.queryUtility(IEventService)

    deviceProperties = PythonPlugin.deviceProperties + (
        'zHBaseScheme',
        'zHBaseUsername',
        'zHBasePassword',
        'zHBaseRestPort',
        'zHBaseMasterPort'
    )

    @defer.inlineCallbacks
    def collect(self, device, log):
        log.debug("Collecting data for device %s", device.id)
        result = {}

        status_url = hbase_rest_url(
            scheme=device.zHBaseScheme,
            port=device.zHBaseRestPort,
            host=device.manageIp,
            endpoint='/status/cluster'
        )
        conf_url = hbase_rest_url(
            scheme=device.zHBaseScheme,
            port=device.zHBaseMasterPort,
            host=device.manageIp,
            endpoint='/dump'
        )
        headers = hbase_headers(
            accept='application/json',
            username=device.zHBaseUsername,
            passwd=device.zHBasePassword
        )
        try:
            result['status'] = yield getPage(status_url, headers=headers)
            result['conf'] = yield getPage(conf_url, headers=headers)
        except Exception, f:
            self.on_error(log, device, f)

        self.on_success(log, device)
        defer.returnValue(result)

    def on_success(self, log, device):
        log.debug('Successfull modeling')
        self._send_event("Successfull modeling", device.id, 0)

    def on_error(self, log, device, failure):
        try:
            e = failure.value
        except:
            e = failure  # no twisted failure
        e = check_error(e, device.id) or e
        self._send_event(str(e), device.id, 5)
        raise e

    def process(self, device, results, log):
        log.info(
            'Modeler %s processing data for device %s',
            self.name(), device.id
        )

        maps = collections.OrderedDict([
            ('hbase_servers', []),
            ('hbase_tables', []),
            ('regions', []),
            ('device', []),
        ])

        # If results.conf is None, it means that the methos is called from
        # monitoring plugin and the conf properties do not need to be updated.
        try:
            conf = ConfWrapper(results['conf']) if results['conf'] else None
            data = json.loads(results['status'])
        except ValueError:
            log.error('HBaseCollector: Error parsing collected data')
            return

        # List of servers
        server_oms = []
        for node in version_diff(data["LiveNodes"]):
            node_id = prepId(node['name'])
            server_oms.append(self._node_om(node, conf, True))

            # List of regions
            region_oms = []
            for region in node["Region"]:
                region_oms.append(self._region_om(region, node_id, conf))

            maps['regions'].append(RelationshipMap(
                compname='hbase_servers/%s' % node_id,
                relname='regions',
                modname=MODULE_NAME['HBaseHRegion'],
                objmaps=region_oms))

        for node in version_diff(data["DeadNodes"]):
            server_oms.append(self._node_om(node, conf))

        maps['hbase_servers'].append(RelationshipMap(
            relname='hbase_servers',
            modname=MODULE_NAME['HBaseRegionServer'],
            objmaps=server_oms))

        # Clear non-existing component events.
        maps['device'].append(ObjectMap({
            'getClearEvents': True
        }))

        log.info(
            'Modeler %s finished processing data for device %s',
            self.name(), device.id
        )
        return list(chain.from_iterable(maps.itervalues()))

    def _node_om(self, node, conf, is_alive=False):
        """Builds HBase Region Server object map"""
        if is_alive:
            title, start_code = (node['name'], node['startCode'])
        else:
            title, start_code = dead_node_name(node)
        object_map = {
            'id': prepId(title),
            'region_name': title,
            'title': title.split(':')[0],
            'start_code': start_code,
            'is_alive': "Up" if is_alive else "Down"
        }
        # If called not from monitoring plugin.
        if conf:
            object_map.update({
                'handler_count': conf.handler_count,
                'memstrore_upper_limit': conf.memstrore_upper_limit,
                'memstrore_lower_limit': conf.memstrore_lower_limit,
                'logflush_interval': conf.logflush_interval
            })
        return ObjectMap(object_map)

    def _region_om(self, region, node_id, conf):
        """Builds HBase Region object map"""
        table, start_key, r_id = region['name'].decode('base64').split(',')
        object_map = {
            'id': node_id + NAME_SPLITTER + prepId(region['name']),
            'title': region['name'].decode('base64'),
            'table': table,
            'start_key': start_key,
            'region_id': r_id,
            'region_hash': region['name']
        }
        # If called not from monitoring plugin.
        if conf:
            object_map.update({
                'memstore_flush_size': convToUnits(conf.memestore_flush_size),
                'max_file_size': convToUnits(conf.max_file_size)
            })
        return ObjectMap(object_map)

    def _send_event(self, reason, id, severity, force=False):
        """
        Send event for device with specified id, severity and
        error message.
        """

        if self._eventService:
            self._eventService.sendEvent(dict(
                summary=reason,
                eventClass='/Status',
                device=id,
                eventKey='HBaseCollector_ConnectionError',
                severity=severity,
            ))
            return True
        else:
            if force or (severity > 0):
                self.device_om = ObjectMap({
                    'setErrorNotification': reason
                })
