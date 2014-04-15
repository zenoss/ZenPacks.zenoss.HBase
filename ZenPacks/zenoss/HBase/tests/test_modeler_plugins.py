##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################


import os
import logging
log = logging.getLogger('zen.HBaseTest')

from Products.DataCollector.ApplyDataMap import ApplyDataMap
from Products.ZenTestCase.BaseTestCase import BaseTestCase

from ZenPacks.zenoss.HBase import NAME_SPLITTER
from ZenPacks.zenoss.HBase.modeler.plugins.HBaseCollector import \
    HBaseCollector
from ZenPacks.zenoss.HBase.modeler.plugins.HBaseTableCollector import \
    HBaseTableCollector
from ZenPacks.zenoss.HBase.tests.utils import test_device, load_data


class MockJar(object):
    """Mock object for x._p_jar.

    Used to trick ApplyDataMap into not aborting transactions after adding
    non-persistent objects. Without doing this, all sub-components will
    cause ugly tracebacks in modeling tests.

    """
    def sync(self):
        pass


class HBaseModelerPluginsTestCase(BaseTestCase):

    def afterSetUp(self):
        super(HBaseModelerPluginsTestCase, self).afterSetUp()

        dc = self.dmd.Devices.createOrganizer('/Server')
        self.d = dc.createInstance('hbase.testDevice')
        self.d.dmd._p_jar = MockJar()
        self.applyDataMap = ApplyDataMap()._applyDataMap

        # Mock clear events function.
        from Products.ZenModel.Device import Device
        mock = lambda *args, **kwargs: None
        Device.getClearEvents = mock
        Device.setClearEvents = mock

    def _loadZenossData(self):
        if hasattr(self, '_loaded'):
            return

        modeler = HBaseCollector()
        modeler_results = dict(
            status=load_data('HBaseCollector.json'),
            conf=None
        )

        for data_map in modeler.process(self.d, modeler_results, log):
            self.applyDataMap(self.d, data_map)

        tab_modeler = HBaseTableCollector()
        tab_modeler_results = load_data('HBaseTableCollector.json')

        for data_map in tab_modeler.process(self.d, tab_modeler_results, log):
            self.applyDataMap(self.d, data_map)

        self._loaded = True

    def test_HBaseRegionServer(self):
        self._loadZenossData()
        region_server = self.d.hbase_servers._getOb('localhost_44451')

        self.assertEquals(region_server.device().id, 'hbase.testDevice')
        self.assertEquals(region_server.start_code, 1111)
        self.assertEquals(region_server.is_alive, 'Up')

    def test_HBaseHRegion(self):
        self._loadZenossData()
        region_server = self.d.hbase_servers._getOb('localhost_44451')
        region = region_server.regions._getOb(
            '%s%s%s' % ('localhost_44451', NAME_SPLITTER, 'LVJPT1QtLCww')
        )

        self.assertEquals(region.device().id, 'hbase.testDevice')
        self.assertEquals(region.server().id, 'localhost_44451')
        self.assertEquals(region.title, '-ROOT-,,0')
        self.assertEquals(region.table, '-ROOT-')
        self.assertEquals(region.start_key, '')
        self.assertEquals(region.region_id, '0')
        self.assertEquals(region.region_hash, 'LVJPT1QtLCww')

    def test_HBaseTable(self):
        self._loadZenossData()
        table = self.d.hbase_tables._getOb('test_table')

        self.assertEquals(table.device().id, 'hbase.testDevice')
        self.assertEquals(table.enabled, None)
        self.assertEquals(table.compaction, None)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(HBaseModelerPluginsTestCase))
    return suite
