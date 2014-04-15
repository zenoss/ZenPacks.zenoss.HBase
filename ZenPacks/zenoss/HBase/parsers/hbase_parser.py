##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import json
import logging

from Products.ZenRRD.CommandParser import CommandParser
from Products.ZenUtils.Utils import getExitMessage

log = logging.getLogger("zen.HBaseParser")


class hbase_parser(CommandParser):
    def processResults(self, cmd, result):
        """
        Parse the results of the datasource.
        """
        if cmd.result.exitCode != 0:
            # No need to send event, as it is done in HBaseRegionServerPlugin.
            log.error("Not able to execute command '{}': {}".format(
                cmd.command,
                getExitMessage(cmd.result.exitCode)
            ))
            return result

        try:
            data = json.loads(cmd.result.output)
        except Exception, e:
            log.error('Error parsing collected data: {}'.format(e))
            return result

        # Create a dict with all metrics containing RPCStatistics,
        # and RegionServerStatistics.
        metrics = {}
        for bean in data.get('beans'):
            metrics.update(bean)

        # Get values for each dp in datasource.
        dp_map = dict([(dp.id, dp) for dp in cmd.points])
        for name, dp in dp_map.items():
            if name in metrics:
                result.values.append((dp, metrics.get(name)))

        log.debug(result.values)
        return result
