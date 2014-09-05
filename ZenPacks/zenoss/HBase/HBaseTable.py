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


class HBaseTable(HBaseComponent):
    meta_type = portal_type = 'HBaseTable'

    enabled = None
    compaction = None
    number_of_col_families = None
    col_family_block_size = None

    _properties = HBaseComponent._properties + (
        {'id': 'enabled', 'type': 'string'},
        {'id': 'compaction', 'type': 'string'},
        {'id': 'number_of_col_families', 'type': 'int'},
        {'id': 'col_family_block_size', 'type': 'string'},
    )

    _relations = HBaseComponent._relations + (
        ('hbase_host', ToOne(
            ToManyCont, 'Products.ZenModel.Device.Device', 'hbase_tables')),
        # ('regions', ToManyCont(
        #     ToOne, MODULE_NAME['HBaseHRegion'], 'table')),
    )

    def device(self):
        return self.hbase_host()


class IHBaseTableInfo(IComponentInfo):
    '''
    API Info interface for HBaseTable.
    '''

    device = schema.Entity(title=_t(u'Device'))
    enabled = schema.TextLine(title=_t(u'Enabled'))
    compaction = schema.TextLine(title=_t(u'Compaction'))
    number_of_col_families = schema.Int(title=_t(u'Number of Column Families'))
    pretty_col_family_block_size = schema.TextLine(title=_t(u'Column Family Block Size'))


class HBaseTableInfo(ComponentInfo):
    ''' API Info adapter factory for HBaseTable '''

    implements(IHBaseTableInfo)
    adapts(HBaseTable)

    enabled = ProxyProperty('enabled')
    compaction = ProxyProperty('compaction')
    number_of_col_families = ProxyProperty('number_of_col_families')
    col_family_block_size = ProxyProperty('col_family_block_size')

    @property
    @info
    def pretty_col_family_block_size(self):
        val = self._object.col_family_block_size
        return val.replace("; ", "</span><br />")
