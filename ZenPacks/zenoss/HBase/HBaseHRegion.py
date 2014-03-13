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


class HBaseHRegion(HBaseComponent):
    meta_type = portal_type = 'HBaseHRegion'

    table = None
    start_key = None
    region_id = None
    region_hash = None

    _properties = HBaseComponent._properties + (
        {'id': 'table', 'type': 'string'},
        {'id': 'start_key', 'type': 'string'},
        {'id': 'region_id', 'type': 'string'},
        {'id': 'region_hash', 'type': 'string'},
    )

    _relations = HBaseComponent._relations + (
        # ('table', ToOne(ToManyCont, MODULE_NAME['HBaseHRegion'], 'regions')),
        ('server', ToOne(ToManyCont, MODULE_NAME['HBaseHRegion'], 'regions')),
    )

    def device(self):
        # return self.table().device()
        return self.server().device()


class IHBaseHRegionInfo(IComponentInfo):
    '''
    API Info interface for HBaseHRegion.
    '''

    device = schema.Entity(title=_t(u'Device'))
    server = schema.Entity(title=_t(u'Region Server'))
    table = schema.TextLine(title=_t(u'Table'))
    start_key = schema.TextLine(title=_t(u'Start Key'))
    region_id = schema.TextLine(title=_t(u'Region ID'))
    region_hash = schema.TextLine(title=_t(u'Hash'))


class HBaseHRegionInfo(ComponentInfo):
    ''' API Info adapter factory for HBaseHRegion '''

    implements(IHBaseHRegionInfo)
    adapts(HBaseHRegion)

    table = ProxyProperty('table')
    start_key = ProxyProperty('start_key')
    region_id = ProxyProperty('region_id')
    region_hash = ProxyProperty('region_hash')

    @property
    @info
    def status(self):
        return self._object.server().is_alive

    @property
    @info
    def server(self):
        return self._object.server()
