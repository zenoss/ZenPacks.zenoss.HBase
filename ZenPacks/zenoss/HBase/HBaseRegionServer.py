##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

from zope.component import adapts
from zope.interface import implements

from Products.ZenRelations.RelSchema import ToOne, ToManyCont

from Products.Zuul.catalog.paths import DefaultPathReporter, relPath
from Products.Zuul.decorators import info
from Products.Zuul.form import schema
from Products.Zuul.infos import ProxyProperty
from Products.Zuul.infos.component import ComponentInfo
from Products.Zuul.interfaces.component import IComponentInfo
from Products.Zuul.utils import ZuulMessageFactory as _t

from . import CLASS_NAME, MODULE_NAME
from .HBaseComponent import HBaseComponent


class HBaseRegionServer(HBaseComponent):
    meta_type = portal_type = 'HBaseRegionServer'

    start_code = None
    is_alive = None
    region_name = None
    handler_count = None
    memstrore_upper_limit = None
    memstrore_lower_limit = None
    logflush_interval = None

    _properties = HBaseComponent._properties + (
        {'id': 'start_code', 'type': 'string'},
        {'id': 'is_alive', 'type': 'string'},
        {'id': 'region_name', 'type': 'string'},
        {'id': 'handler_count', 'type': 'string'},
        {'id': 'memstrore_upper_limit', 'type': 'string'},
        {'id': 'memstrore_lower_limit', 'type': 'string'},
        {'id': 'logflush_interval', 'type': 'string'},
    )

    _relations = HBaseComponent._relations + (
        ('hbase_host', ToOne(
            ToManyCont, 'Products.ZenModel.Device.Device', 'hbase_servers')),
        ('regions', ToManyCont(
            ToOne, MODULE_NAME['HBaseHRegion'], 'server')),
    )

    def device(self):
        return self.hbase_host()


class IHBaseRegionServerInfo(IComponentInfo):
    '''
    API Info interface for HBaseRegionServer.
    '''

    device = schema.Entity(title=_t(u'Device'))
    start_code = schema.TextLine(title=_t(u'Start Code'))
    handler_count = schema.TextLine(title=_t(u'Handler Count'))
    memstrore_upper_limit = schema.TextLine(title=_t(u'Memstrore Upper Limit'))
    memstrore_lower_limit = schema.TextLine(title=_t(u'Memstrore Lower Limit'))
    logflush_interval = schema.TextLine(title=_t(u'Log Flush Interval'))


class HBaseRegionServerInfo(ComponentInfo):
    ''' API Info adapter factory for HBaseRegionServer '''

    implements(IHBaseRegionServerInfo)
    adapts(HBaseRegionServer)

    start_code = ProxyProperty('start_code')
    is_alive = ProxyProperty('is_alive')
    region_name = ProxyProperty('region_name')
    handler_count = ProxyProperty('handler_count')
    memstrore_upper_limit = ProxyProperty('memstrore_upper_limit')
    memstrore_lower_limit = ProxyProperty('memstrore_lower_limit')
    logflush_interval = ProxyProperty('logflush_interval')

    @property
    @info
    def status(self):
        return self.is_alive

    @property
    @info
    def region_ids(self):
        return self._object.regions.objectIds()
