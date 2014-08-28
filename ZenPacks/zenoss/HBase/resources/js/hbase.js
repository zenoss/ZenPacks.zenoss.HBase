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
ZC.registerName('HBaseHRegion', _t('HBase Region'), _t('HBase Regions'));

Ext.apply(Zenoss.render, {
    linkFromSubgrid: function(value, metaData, record) {
        if (this.subComponentGridPanel) {
            return Zenoss.render.link(record.data.uid, null, value);
        } else {
            return value;
        }
    },

    trueFalse: function(value) {
        var str = value == 'true' ? 'clear' : '';
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
                {name: 'region_name'},
                {name: 'handler_count'},
                {name: 'memstrore_upper_limit'},
                {name: 'memstrore_lower_limit'},
                {name: 'logflush_interval'}
            ],
            columns: [{
                id: 'severity',
                dataIndex: 'severity',
                header: _t('Events'),
                renderer: Zenoss.render.severity,
                width: 50
            },{
                id: 'name',
                dataIndex: 'region_name',
                header: _t('Name')
            },{
                id: 'start_code',
                dataIndex: 'start_code',
                header: _t('Start Code'),
                width: 300
            },{
                id: 'handler_count',
                dataIndex: 'handler_count',
                header: _t('Handler Count')
            },{
                id: 'memstrore_upper_limit',
                dataIndex: 'memstrore_upper_limit',
                header: _t('Memstrore Upper Limit'),
                width: 140
            },{
                id: 'memstrore_lower_limit',
                dataIndex: 'memstrore_lower_limit',
                header: _t('Memstrore Lower Limit'),
                width: 140
            },{
                id: 'logflush_interval',
                dataIndex: 'logflush_interval',
                header: _t('Log Flush Interval'),
                width: 110
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
                {name: 'number_of_col_families'},
                {name: 'col_family_block_size'},
                {name: 'enabled'},
                {name: 'compaction'}
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
                header: _t('Name')
            },{
                id: 'number_of_col_families',
                dataIndex: 'number_of_col_families',
                header: _t('Number of Column Families'),
                width: 150
            },{
                id: 'col_family_block_size',
                dataIndex: 'col_family_block_size',
                header: _t('Column Family Block Size'),
                width: 200
            },{
                id: 'compaction',
                dataIndex: 'compaction',
                header: _t('Compaction')
            },{
                id: 'enabled',
                dataIndex: 'enabled',
                header: _t('Enabled'),
                renderer: Zenoss.render.trueFalse,
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
        ZC.HBaseTablePanel.superclass.constructor.call(this, config);
    }
});

Ext.reg('HBaseTablePanel', ZC.HBaseTablePanel);

/* HBaseHRegion */
ZC.HBaseHRegionPanel = Ext.extend(ZC.ComponentGridPanel, {
    subComponentGridPanel: false,

    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            autoExpandColumn: 'region_id',
            componentType: 'HBaseHRegion',
            fields: [
                {name: 'uid'},
                {name: 'severity'},
                {name: 'status'},
                {name: 'usesMonitorAttribute'},
                {name: 'monitor'},
                {name: 'monitored'},
                {name: 'locking'},
                {name: 'server'},
                {name: 'table'},
                {name: 'start_key'},
                {name: 'region_id'},
                {name: 'memstore_flush_size'},
                {name: 'max_file_size'}
            ],
            columns: [{
                id: 'severity',
                dataIndex: 'severity',
                header: _t('Events'),
                renderer: Zenoss.render.severity,
                width: 50
            },{
                id: 'table',
                dataIndex: 'table',
                header: _t('Table'),
                width: 120
            },{
                id: 'start_key',
                dataIndex: 'start_key',
                header: _t('Start Key'),
                width: 60
            },{
                id: 'region_id',
                dataIndex: 'region_id',
                header: _t('Region ID'),
                renderer: Zenoss.render.linkFromSubgrid,
                width: 290
            },{
                id: 'server',
                dataIndex: 'server',
                header: _t('Region Server'),
                renderer: Zenoss.render.linkFromGrid,
                width: 170
            },{
                id: 'memstore_flush_size',
                dataIndex: 'memstore_flush_size',
                header: _t('Memstore Flush Size'),
                width: 130
            },{
                id: 'max_file_size',
                dataIndex: 'max_file_size',
                header: _t('Max File Size')
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
        ZC.HBaseHRegionPanel.superclass.constructor.call(this, config);
    }
});

Ext.reg('HBaseHRegionPanel', ZC.HBaseHRegionPanel);


/* Subcomponent Panels */
/* HBaseHRegion */
Zenoss.nav.appendTo('Component', [{
    id: 'regions',
    text: _t('Regions'),
    xtype: 'HBaseHRegionPanel',
    subComponentGridPanel: true,
    filterNav: function(navpanel) {
         switch (navpanel.refOwner.componentType) {
            case 'HBaseRegionServer': return true;
            default: return false;
         }
    },
    setContext: function(uid) {
        ZC.HBaseHRegionPanel.superclass.setContext.apply(this, [uid]);
    }
}]);


/* Select Field for zHBaseScheme */
Zenoss.form.SelectScheme = Ext.extend(Ext.form.ComboBox, {
    constructor: function(config){
        Ext.applyIf(config, {
            editable: false,
            allowBlank: false,
            triggerAction: 'all',
            typeAhead: false,
            forceSelection: true,
            store: ['http', 'https']
        });
        Zenoss.form.Select.superclass.constructor.call(this, config);
    }
});
/* Ext.version will be defined in ExtJS3 and undefined in ExtJS4. */
Zenoss.zproperties.registerZPropertyType('scheme', {xtype: 'scheme'});
if (Ext.version === undefined) {
    Ext.reg('scheme', 'Zenoss.form.SelectScheme');
} else {
    Ext.reg('scheme', Zenoss.form.SelectScheme);
}

})();
