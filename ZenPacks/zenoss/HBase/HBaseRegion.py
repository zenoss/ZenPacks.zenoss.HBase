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


class HBaseRegion(HBaseComponent):
    meta_type = portal_type = 'HBaseRegion'

    _properties = HBaseComponent._properties + (
    )

    _relations = HBaseComponent._relations + (
        # ('table', ToOne(ToManyCont, MODULE_NAME['HBaseRegion'], 'regions')),
        ('server', ToOne(ToManyCont, MODULE_NAME['HBaseRegion'], 'regions')),
    )

    def device(self):
        # return self.table().device()
        return self.server().device()


class IHBaseRegionInfo(IComponentInfo):
    '''
    API Info interface for HBaseRegion.
    '''

    pass


class HBaseRegionInfo(ComponentInfo):
    ''' API Info adapter factory for HBaseRegion '''

    implements(IHBaseRegionInfo)
    adapts(HBaseRegion)

    @property
    @info
    def status(self):
        if (self._object.server().is_alive == "yes"):
            return "Up"
        return "Down"
