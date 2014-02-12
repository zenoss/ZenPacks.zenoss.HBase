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

    start_time = None

    _properties = HBaseComponent._properties + (
        {'id': 'start_time', 'type': 'string'},
    )

    _relations = HBaseComponent._relations + (
        ('hbase_host', ToOne(
            ToManyCont, 'Products.ZenModel.Device.Device', 'hbase_servers')),
    )

    def device(self):
        return self.hbase_host()


class IHBaseRegionServerInfo(IComponentInfo):
    '''
    API Info interface for HBaseRegionServer.
    '''

    start_time = schema.TextLine(title=_t(u'Start time'))


class HBaseRegionServerInfo(ComponentInfo):
    ''' API Info adapter factory for HBaseRegionServer '''

    implements(IHBaseRegionServerInfo)
    adapts(HBaseRegionServer)

    start_time = ProxyProperty('start_time')
