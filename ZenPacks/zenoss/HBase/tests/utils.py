##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import os.path

from zope.event import notify
from Products.Zuul.catalog.events import IndexingEvent


def load_data(filename):
    path = os.path.join(os.path.dirname(__file__), 'data', filename)
    with open(path, 'r') as f:
        return f.read()


def add_obj(relationship, obj):
    """
    Add obj to relationship, index it, then returns the persistent
    object.
    """
    relationship._setObject(obj.id, obj)
    obj = relationship._getOb(obj.id)
    obj.index_object()
    notify(IndexingEvent(obj))
    return obj


def test_device(dmd, factor=1):
    """
     Return an example SolarisMonitorDevice with a set of example components.
    """

    from ZenPacks.zenoss.HBase.HBaseRegionServer import HBaseRegionServer
    from ZenPacks.zenoss.HBase.HBaseRegion import HBaseRegion
    from ZenPacks.zenoss.HBase.HBaseTable import HBaseTable

    dc = dmd.Devices.createOrganizer('/Server')

    device = dc.createInstance('hbase_test_device')
    device.setPerformanceMonitor('localhost')
    device.index_object()
    notify(IndexingEvent(device))

    # Region Servers
    for region_server_id in range(factor):
        region_server = add_obj(
            device.hbase_servers,
            HBaseRegionServer('region_server%s' % (region_server_id))
        )

        # Regions
        for region_id in range(factor):
            region = add_obj(
                region_server.regions,
                HBaseRegion('region%s-%s' % (region_server_id, region_id))
            )

    # Tables
    for table_id in range(factor):
        table = add_obj(
            device.hbase_tables,
            HBaseTable('table%s' % (table_id))
        )

    return device
