##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import json
import os
import re

from base64 import encodestring
from zope.event import notify

from Products.AdvancedQuery import Eq, Or
from Products.ZenUtils.Utils import prepId
from Products.Zuul.interfaces import ICatalogTool
from Products.Zuul.catalog.events import IndexingEvent


def here(dir, base=os.path.dirname(__file__)):
    return os.path.join(base, dir)


def add_local_lib_path():
    '''
    Helper to add the ZenPack's lib directory to sys.path.
    '''
    #import sys
    import site

    site.addsitedir(here('lib'))
    #sys.path.append(here('lib'))

add_local_lib_path()


def updateToMany(relationship, root, type_, ids):
    '''
    Update ToMany relationship given search root, type and ids.

    This is a general-purpose function for efficiently building
    non-containing ToMany relationships.
    '''
    root = root.primaryAq()

    new_ids = set(map(prepId, ids))
    current_ids = set(o.id for o in relationship.objectValuesGen())
    changed_ids = new_ids.symmetric_difference(current_ids)

    query = Or(*(Eq('id', x) for x in changed_ids))

    obj_map = {}
    for result in ICatalogTool(root).search(types=[type_], query=query):
        obj_map[result.id] = result.getObject()

    for id_ in new_ids.symmetric_difference(current_ids):
        obj = obj_map.get(id_)
        if not obj:
            continue

        if id_ in new_ids:
            relationship.addRelation(obj)
        else:
            relationship.removeRelation(obj)

        # Index remote object. It might have a custom path reporter.
        notify(IndexingEvent(obj, 'path', False))

        # For componentSearch. Would be nice if we could target
        # idxs=['getAllPaths'], but there's a chance that it won't exist
        # yet.
        obj.index_object()


def updateToOne(relationship, root, type_, id_):
    '''
    Update ToOne relationship given search root, type and ids.

    This is a general-purpose function for efficiently building
    non-containing ToOne relationships.
    '''
    old_obj = relationship()

    # Return with no action if the relationship is already correct.
    if (old_obj and old_obj.id == id_) or (not old_obj and not id_):
        return
    # Remove current object from relationship.
    if old_obj:
        relationship.removeRelation()

        # Index old object. It might have a custom path reporter.
        notify(IndexingEvent(old_obj.primaryAq(), 'path', False))

    # No need to find new object if id_ is empty.
    if not id_:
        return

    # Find and add new object to relationship.
    root = root.primaryAq()
    query = Eq('id', id_)

    for result in ICatalogTool(root).search(types=[type_], query=query):
        new_obj = result.getObject()
        relationship.addRelation(new_obj)

        # Index remote object. It might have a custom path reporter.
        notify(IndexingEvent(new_obj.primaryAq(), 'path', False))

        # For componentSearch. Would be nice if we could target
        # idxs=['getAllPaths'], but there's a chance that it won't exist
        # yet.
        new_obj.index_object()

    return

# HBase default ports.
MASTER_INFO_PORT = '60010'
REGIONSERVER_INFO_PORT = '60030'


def hbase_rest_url(port, host, endpoint):
    """
    Constructs URL to access HBase REST interface.
    """
    url = 'http://{}:{}{}'.format(host, port, endpoint)
    return url


def hbase_headers(accept, username, passwd):
    """
    Constructs headers to access HBase REST interface.
    """
    auth = encodestring(
        '{}:{}'.format(username, passwd)
    )
    authHeader = "Basic " + auth.strip()
    return {
        "Accept": accept,
        "Authorization": authHeader,
        'Proxy-Authenticate': authHeader
    }


def dead_node_name(node):
    """
    Parses the dead server name in format of 'domain,port,startcode'
    into title and start code.
    """
    try:
        name, port, start_code = node.split(',')
        title = '{0}:{1}'.format(name, port)
        return title, start_code
    except:
        return node, node


def matcher(res, rule, default=''):
    """
    Return the value in the first group or empty string if no match found.

    @param res: result of getPage query
    @type res: str
    @param rule: regular expression for value matching
    @type rule: str
    @return: string value
    """
    res = res.replace('\n', '').replace(' ', '')
    matcher = re.compile(rule)
    match = matcher.match(res)
    if match:
        return match.group(1)
    return default


class ConfWrapper(object):
    """
    Wrapper for region server configuration properties.
    """
    def __init__(self, dump):
        """
        Match the needed properties to their values.

        @param dump: result of getPage query
        @type dump: str
        """
        self.conf = matcher(dump, r'.+<configuration>(.+)</configuration>')
        self.handler_count = matcher(self.conf, self.rule(
            'hbase.regionserver.handler.count'
        ))  # Defaults to 10.
        self.memstrore_upper_limit = matcher(self.conf, self.rule(
            'hbase.regionserver.global.memstore.upperLimit'
        ))  # Defaults to 0.4.
        self.memstrore_lower_limit = matcher(self.conf, self.rule(
            'hbase.regionserver.global.memstore.lowerLimit'
        ))  # Defaults to 0.35.
        self.logflush_interval = matcher(self.conf, self.rule(
            'hbase.regionserver.optionallogflushinterval'
        ))  # Defaults to 1000.
        self.memestore_flush_size = matcher(self.conf, self.rule(
            'hbase.hregion.memstore.flush.size'
        ))  # Defaults to 134217728.
        self.max_file_size = matcher(self.conf, self.rule(
            'hbase.hregion.max.filesize'
        ))  # Defaults to 10737418240.

    def rule(self, property_name):
        """
        Construct a regex rule for the specified property.

        @param property_name: the name of the property to be found
        @type property_name: str
        """
        return r'.+<name>{}</name><value>(.+?)</value>'.format(property_name)
