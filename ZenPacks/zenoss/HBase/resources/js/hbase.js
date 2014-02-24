/*****************************************************************************
 *
 * Copyright (C) Zenoss, Inc. 2013, all rights reserved.
 *
 * This content is made available according to terms specified in
 * License.zenoss under the directory where your Zenoss product is installed.
 *
 ****************************************************************************/

(function(){

var ZC = Ext.ns('Zenoss.component');
var ZD = Ext.ns('Zenoss.devices');

ZC.registerName('HBaseRegionServer', _t('HBase Region Server'), _t('HBase Region Servers'));
ZC.registerName('HBaseTable', _t('HBase Table'), _t('HBase Tables'));
ZC.registerName('HBaseRegion', _t('HBase Region'), _t('HBase Regions'));

Ext.apply(Zenoss.render, {
    linkFromSubgrid: function(value, metaData, record) {
        if (this.subComponentGridPanel) {
            return Zenoss.render.link(record.data.uid, null, value);
        } else {
            return value;
        }
    },

    trueFalse: function(value) {
        var str = value == 'yes' ? 'clear' : '';
        return '<div class="severity-icon-small '+ str +'"><'+'/div>';
    }
});

/* HBaseRegionServer */
ZC.HBaseRegionServerPanel = Ext.extend(ZC.ComponentGridPanel, {
    subComponentGridPanel: false,

    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            autoExpandColumn: 'name',
            componentType: 'HBaseRegionServer',
            fields: [
                {name: 'uid'},
                {name: 'name'},
                {name: 'severity'},
                {name: 'status'},
                {name: 'usesMonitorAttribute'},
                {name: 'monitor'},
                {name: 'monitored'},
                {name: 'locking'},
                {name: 'start_code'},
            ],
            columns: [{
                id: 'severity',
                dataIndex: 'severity',
                header: _t('Events'),
                renderer: Zenoss.render.severity,
                width: 50
            },{
                id: 'name',
                dataIndex: 'name',
                header: _t('Name'),
            },{
                id: 'start_code',
                dataIndex: 'start_code',
                header: _t('Start Code'),
                width: 300
            },{
                id: 'status',
                dataIndex: 'status',
                header: _t('Status'),
                renderer: Zenoss.render.pingStatus,
                width: 60
            },{
                id: 'monitored',
                dataIndex: 'monitored',
                header: _t('Monitored'),
                renderer: Zenoss.render.checkbox,
                width: 60
            },{
                id: 'locking',
                dataIndex: 'locking',
                header: _t('Locking'),
                renderer: Zenoss.render.locking_icons,
                width: 60
            }]
        });
        ZC.HBaseRegionServerPanel.superclass.constructor.call(this, config);
    }
});

Ext.reg('HBaseRegionServerPanel', ZC.HBaseRegionServerPanel);

/* HBaseTable */
ZC.HBaseTablePanel = Ext.extend(ZC.ComponentGridPanel, {
    subComponentGridPanel: false,

    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            autoExpandColumn: 'name',
            componentType: 'HBaseTable',
            fields: [
                {name: 'uid'},
                {name: 'name'},
                {name: 'status'},
                {name: 'severity'},
                {name: 'usesMonitorAttribute'},
                {name: 'monitor'},
                {name: 'monitored'},
                {name: 'locking'},
                {name: 'start_code'},
                {name: 'is_alive'},
            ],
            columns: [{
                id: 'severity',
                dataIndex: 'severity',
                header: _t('Events'),
                renderer: Zenoss.render.severity,
                width: 50
            },{
                id: 'name',
                dataIndex: 'name',
                header: _t('Name'),
            },{
                id: 'monitored',
                dataIndex: 'monitored',
                header: _t('Monitored'),
                renderer: Zenoss.render.checkbox,
                width: 60
            },{
                id: 'locking',
                dataIndex: 'locking',
                header: _t('Locking'),
                renderer: Zenoss.render.locking_icons,
                width: 60
            }]
        });
        ZC.HBaseTablePanel.superclass.constructor.call(this, config);
    }
});

Ext.reg('HBaseTablePanel', ZC.HBaseTablePanel);

/* HBaseRegion */
ZC.HBaseRegionPanel = Ext.extend(ZC.ComponentGridPanel, {
    subComponentGridPanel: false,

    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            autoExpandColumn: 'name',
            componentType: 'HBaseRegion',
            fields: [
                {name: 'uid'},
                {name: 'name'},
                {name: 'severity'},
                {name: 'status'},
                {name: 'usesMonitorAttribute'},
                {name: 'monitor'},
                {name: 'monitored'},
                {name: 'locking'},
            ],
            columns: [{
                id: 'severity',
                dataIndex: 'severity',
                header: _t('Events'),
                renderer: Zenoss.render.severity,
                width: 50
            },{
                id: 'name',
                dataIndex: 'name',
                header: _t('Name'),
            },{
                id: 'status',
                dataIndex: 'status',
                header: _t('Status'),
                renderer: Zenoss.render.pingStatus,
                width: 60
            },{
                id: 'monitored',
                dataIndex: 'monitored',
                header: _t('Monitored'),
                renderer: Zenoss.render.checkbox,
                width: 60
            },{
                id: 'locking',
                dataIndex: 'locking',
                header: _t('Locking'),
                renderer: Zenoss.render.locking_icons,
                width: 60
            }]
        });
        ZC.HBaseRegionPanel.superclass.constructor.call(this, config);
    }
});

Ext.reg('HBaseRegionPanel', ZC.HBaseRegionPanel);


/* Subcomponent Panels */
/* HBaseRegion */
Zenoss.nav.appendTo('Component', [{
    id: 'regions',
    text: _t('Regions'),
    xtype: 'HBaseRegionPanel',
    subComponentGridPanel: true,
    filterNav: function(navpanel) {
         switch (navpanel.refOwner.componentType) {
            case 'HBaseRegionServer': return true;
            default: return false;
         }
    },
    setContext: function(uid) {
        ZC.HBaseRegionPanel.superclass.setContext.apply(this, [uid]);
    }
}]);

})();
