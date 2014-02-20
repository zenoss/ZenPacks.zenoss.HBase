##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

from zope.component import adapts
from zope.interface import implements

from Products.ZenRelations.RelSchema import ToOne, ToMany, ToManyCont

from Products.Zuul.catalog.paths import DefaultPathReporter, relPath
from Products.Zuul.decorators import info
from Products.Zuul.form import schema
from Products.Zuul.infos import ProxyProperty
from Products.Zuul.infos.component import ComponentInfo
from Products.Zuul.interfaces.component import IComponentInfo
from Products.Zuul.utils import ZuulMessageFactory as _t

from . import CLASS_NAME, MODULE_NAME
from .HBaseComponent import HBaseComponent
from .utils import updateToMany, updateToOne


class HBaseRegionServer(HBaseComponent):
    meta_type = portal_type = 'HBaseRegionServer'

    start_code = None
    is_alive = None

    _properties = HBaseComponent._properties + (
        {'id': 'start_code', 'type': 'string'},
        {'id': 'is_alive', 'type': 'string'},
    )

    _relations = HBaseComponent._relations + (
        ('hbase_host', ToOne(
            ToManyCont, 'Products.ZenModel.Device.Device', 'hbase_servers')),
        ('regions', ToManyCont(
            ToOne, MODULE_NAME['HBaseRegion'], 'server')),
    )

    def device(self):
        return self.hbase_host()

    # def getStatus(self):
    #     return "Up" # (self.is_alive == "yes")


class IHBaseRegionServerInfo(IComponentInfo):
    '''
    API Info interface for HBaseRegionServer.
    '''

    start_code = schema.TextLine(title=_t(u'Start code'))


class HBaseRegionServerInfo(ComponentInfo):
    ''' API Info adapter factory for HBaseRegionServer '''

    implements(IHBaseRegionServerInfo)
    adapts(HBaseRegionServer)

    start_code = ProxyProperty('start_code')
    is_alive = ProxyProperty('is_alive')

    @property
    @info
    def status(self):
        return self.is_alive
