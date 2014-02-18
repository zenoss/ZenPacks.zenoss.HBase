##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

''' Models discovery tree for HBase. '''

import json
import collections
import zope.component
from itertools import chain
from twisted.web.client import getPage

from Products.DataCollector.plugins.CollectorPlugin import PythonPlugin
from Products.DataCollector.plugins.DataMaps import ObjectMap, RelationshipMap
from Products.ZenCollector.interfaces import IEventService
from Products.ZenUtils.Utils import prepId
from ZenPacks.zenoss.HBase import MODULE_NAME, NAME_SPLITTER
from ZenPacks.zenoss.HBase.utils import hbase_rest_url


class HBaseCollector(PythonPlugin):
    '''
    PythonCollector plugin for modelling device components
    '''
    is_clear_run = True
    device_om = None

    _eventService = zope.component.queryUtility(IEventService)

    deviceProperties = PythonPlugin.deviceProperties + (
        'zHBaseUsername',
        'zHBasePasword',
        'zHBasePort'
        )

    def collect(self, device, log):
        log.info("Collecting data for device %s", device.id)

        url = hbase_rest_url(
            user=device.zHBaseUsername,
            passwd=device.zHBasePasword,
            port=device.zHBasePort,
            host=device.manageIp,
            endpoint='/status/cluster'
        )

        res = getPage(url, headers={'Accept': 'application/json'})
        res.addCallbacks(
            lambda r: self.on_success(log, device, r),
            lambda f: self.on_error(log, device, f)
        )
        return res

    def on_success(self, log, device, data):
        log.info('Successfull modeling')
        self._send_event("Successfull modeling", device.id, 0)
        return data

    def on_error(self, log, device, failure):
        try:
            e = failure.value
        except:
            e = failure  # no twisted failure
        log.error(e)
        self._send_event(str(e).capitalize(), device.id, 5)
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

        data = json.loads(results)

        # List of servers
        server_oms = []
        for node in data["LiveNodes"]:
            node_id = prepId(node['name'])
            server_oms.append(self._node_om(node, True))

            # List of regions
            region_oms = []
            for region in node["Region"]:
                region_oms.append(self._region_om(region, node_id))

            maps['regions'].append(RelationshipMap(
                compname='hbase_servers/%s' % node_id,
                relname='regions',
                modname=MODULE_NAME['HBaseRegion'],
                objmaps=region_oms))

        for node in data["DeadNodes"]:
            server_oms.append(self._node_om(node))

        maps['hbase_servers'].append(RelationshipMap(
            relname='hbase_servers',
            modname=MODULE_NAME['HBaseRegionServer'],
            objmaps=server_oms))

        log.info(
            'Modeler %s finished processing data for device %s',
            self.name(), device.id
        )

        return list(chain.from_iterable(maps.itervalues()))

    def _node_om(self, node, is_alive = False):
        """Builds HBase Region Server object map"""

        if is_alive:
            return ObjectMap({
                'id': prepId(node['name']),
                'title': node['name'],
                'start_code': node['startCode'],
                'is_alive': "Up"
            })
        else:
            return ObjectMap({
                'id': prepId(node),
                'title': node,
                'start_code': node,
                'is_alive': "Down"
            })

    def _region_om(self, region, node_id):
        """Builds HBase Region object map"""
        return ObjectMap({
            'id': node_id + NAME_SPLITTER + prepId(region['name']),
            'title': region['name']
        })

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
                eventKey='ConnectionError',
                severity=severity,
                ))
            return True
        else:
            if force or (severity > 0):
                self.device_om = ObjectMap({
                    'setErrorNotification': reason
                })
