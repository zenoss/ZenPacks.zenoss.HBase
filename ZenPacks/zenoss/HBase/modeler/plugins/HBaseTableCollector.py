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


class HBaseTableCollector(PythonPlugin):
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

        user = device.zHBaseUsername
        port = device.zHBasePort
        host = device.manageIp
        passwd = device.zHBasePasword

        url = 'http://'
        if user:
            url += user
        if passwd:
            url += ":" + passwd + "@"
        url += host + ':' + port + '/'

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
            ('hbase_tables', [])
        ])

        data = json.loads(results)

        # List of tables
        tables_oms = []
        for table in data["table"]:
            tables_oms.append(self._table_om(table))

        maps['hbase_tables'].append(RelationshipMap(
            relname='hbase_tables',
            modname=MODULE_NAME['HBaseTable'],
            objmaps=tables_oms))
        log.info(
            'Modeler %s finished processing data for device %s',
            self.name(), device.id
        )

        return list(chain.from_iterable(maps.itervalues()))

    def _table_om(self, table):
        """Builds HBase Region Server object map"""

        return ObjectMap({
            'id': prepId(table['name']),
            'title': table['name'],
            # 'compaction': table['name'],
            # 'enabled': "yes"
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
