##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import functools

from zope.component import subscribers

from Products.Five import zcml

from Products.ZenTestCase.BaseTestCase import BaseTestCase
from Products.ZenUtils.guid.interfaces import IGUIDManager
from Products.ZenUtils.Utils import unused

from ZenPacks.zenoss.HBase.tests.utils import test_device


def require_impact(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            import ZenPacks.zenoss.Impact
            unused(ZenPacks.zenoss.Impact)
        except ImportError:
            return

        return f(*args, **kwargs)

    return wrapper


def impacts_for(thing):
    '''
    Return a two element tuple.

    First element is a list of object ids impacted by thing. Second element is
    a list of object ids impacting thing.
    '''
    try:
        from ZenPacks.zenoss.Impact.impactd.interfaces import \
            IRelationshipDataProvider

    except ImportError:
        return ([], [])

    impacted_by = []
    impacting = []

    guid_manager = IGUIDManager(thing.getDmd())
    for subscriber in subscribers([thing], IRelationshipDataProvider):
        for edge in subscriber.getEdges():
            source = guid_manager.getObject(edge.source)
            impacted = guid_manager.getObject(edge.impacted)
            if source == thing:
                impacted_by.append(impacted.id)
            elif impacted == thing:
                impacting.append(source.id)

    return (impacted_by, impacting)


class TestImpact(BaseTestCase):
    '''
    Test suite for all Impact adapters.
    '''

    def afterSetUp(self):
        super(TestImpact, self).afterSetUp()

        try:
            import ZenPacks.zenoss.DynamicView
            zcml.load_config('configure.zcml', ZenPacks.zenoss.DynamicView)
        except ImportError:
            pass

        try:
            import ZenPacks.zenoss.Impact
            zcml.load_config('meta.zcml', ZenPacks.zenoss.Impact)
            zcml.load_config('configure.zcml', ZenPacks.zenoss.Impact)
        except ImportError:
            pass

        import ZenPacks.zenoss.HBase
        zcml.load_config('configure.zcml', ZenPacks.zenoss.HBase)

    def device(self):
        if not hasattr(self, '_device'):
            self._device = test_device(self.dmd, factor=1)

        return self._device

    @require_impact
    def test_HBaseRegionServerImpacts(self):
        region_server = self.device().getObjByPath(
            'hbase_servers/region_server0')

        impacts, impacted_by = impacts_for(region_server)

        self.assertTrue('hbase_test_device' in impacts)
        self.assertTrue('region0-0' in impacted_by)

    @require_impact
    def test_HBaseRegionImpacts(self):
        region = self.device().getObjByPath(
            'hbase_servers/region_server0/regions/region0-0')

        impacts, impacted_by = impacts_for(region)

        self.assertTrue('region_server0' in impacts)

    @require_impact
    def test_HBaseTableImpacts(self):
        table = self.device().getObjByPath(
            'hbase_tables/table0')

        impacts, impacted_by = impacts_for(table)

        self.assertTrue('hbase_test_device' in impacts)
