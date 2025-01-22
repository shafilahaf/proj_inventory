odoo.define('inventorymodule.DisableArchiveOption', function(require) {
    "use strict";
    var ListController = require('web.ListController');
    var core = require('web.core');
    var _t = core._t;

    ListController.include({
        _getActionMenuItems: function (state) {
            if (!this.hasActionMenus || !this.selectedRecords.length) {
                return null;
            }
            const props = this._super(...arguments);
            const otherActionItems = [];
            if (this.isExportEnable) {
                otherActionItems.push({
                    description: _t("Export"),
                    callback: () => this._onExportData()
                });
            }
            if (this.modelName != 'ae.inventory'){
                if (this.archiveEnabled) {
                    otherActionItems.push({
                        description: _t("Archive"),
                        callback: () => this._toggleArchiveState(true)
                    }, {
                        description: _t("Unarchive"),
                        callback: () => this._toggleArchiveState(false)
                    });
                }    
            }
            if (this.activeActions.delete) {
                otherActionItems.push({
                    description: _t("Delete"),
                    callback: () => this._onDeleteSelectedRecords()
                });
            }
            return Object.assign(props, {
                items: Object.assign({}, this.toolbarActions, { other: otherActionItems }),
                context: state.getContext(),
                domain: state.getDomain(),
                isDomainSelected: this.isDomainSelected,
            });
        },
    });

});