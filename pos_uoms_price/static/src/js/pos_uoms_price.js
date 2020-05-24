odoo.define('pos_retail.multi_unit_of_measure', function (require) {
    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var _t = core._t;

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        init_from_JSON: function (json) {
            _super_orderline.init_from_JSON.apply(this, arguments);
            if (json.uom_id) {
                this.uom_id = json.uom_id;
                var unit = this.pos.units_by_id[json.uom_id]
                if (unit) {
                    this.product.uom_id = [unit['id'], unit['name']];
                }
            }
        },
        export_as_JSON: function () {
            var json = _super_orderline.export_as_JSON.apply(this, arguments);
            if (this.uom_id) {
                json.uom_id = this.uom_id
            }
            return json;
        },
        get_unit: function () {
            if (!this.uom_id) {
                return _super_orderline.get_unit.apply(this, arguments);
            } else {
                var unit_id = this.uom_id
                return this.pos.units_by_id[unit_id];
            }
        },
        is_multi_unit_of_measure: function () {
            var uom_items = this.pos.uoms_prices_by_product_tmpl_id[this.product.product_tmpl_id]
            if (!uom_items) {
                return false;
            }
            if (uom_items.length > 0) {
                return true;
            } else {
                return false;
            }
        },
        // we're keep price when change uom id
        // core odoo will modify price when set quantity, auto get price from pricelist
        set_quantity: function (quantity, keep_price) {
            if (this.uom_id) {
                keep_price = 'keep price because changed uom id'
            }
            _super_orderline.set_quantity.call(this, quantity, keep_price);
            this.trigger('change', this);
        }
    });

    var button_choice_uom = screens.ActionButtonWidget.extend({
        template: 'button_choice_uom',
        button_click: function () {
            var order = this.pos.get_order()
            if (order) {
                var selected_orderline = order.selected_orderline;
                if (selected_orderline) {
                    var product = selected_orderline.product;
                    var uom_items = this.pos.uoms_prices_by_product_tmpl_id[product.product_tmpl_id]
                    if (!uom_items) {
                        return this.pos.gui.show_popup('error', {
                            title: '!!! Warning !!!',
                            body: product['display_name'] + ' have ' + product['uom_id'][1] + ' only.'
                        });
                    }
                    var list = [];
                    for (var i = 0; i < uom_items.length; i++) {
                        var item = uom_items[i];
                        list.push({
                            'label': item.uom_id[1],
                            'item': item,
                        });
                    }
                    if (list.length) {
                        return this.gui.show_popup('selection', {
                            title: _t('Select Unit of measure'),
                            list: list,
                            confirm: function (item) {
                                selected_orderline.set_unit_price(item['price'])
                                selected_orderline.uom_id = item['uom_id'][0];
                                selected_orderline.trigger('change', selected_orderline);
                                selected_orderline.trigger('update:OrderLine');
                            }
                        });
                    } else {
                        return this.pos.gui.show_popup('error', {
                            title: '!!! Warning !!!',
                            body: product['display_name'] + ' have ' + product['uom_id'][1] + ' only.'
                        });
                    }
                } else {
                    return this.pos.gui.show_popup('error', {
                        title: '!!! Warning !!!',
                        body: 'Please select line want change unit of measure'
                    });
                }
            } else {
                return this.pos.gui.show_popup('error', {
                    title: '!!! Warning !!!',
                    body: 'Order null'
                });
            }

        }
    });
    screens.define_action_button({
        'name': 'button_choice_uom',
        'widget': button_choice_uom,
        'condition': function () {
            return this.pos.uoms_prices.length && this.pos.uoms_prices.length > 0;
        }
    });

    models.load_models([
        {
            model: 'product.uom.price',
            fields: [],
            domain: [],
            context: {'pos': true},
            loaded: function (self, uoms_prices) {
                self.uom_price_id = {}
                self.uoms_prices_by_product_tmpl_id = {}
                self.uoms_prices = uoms_prices;
                for (var i = 0; i < uoms_prices.length; i++) {
                    var item = uoms_prices[i];
                    if (item.product_tmpl_id) {
                        self.uom_price_id[item.id] = item;
                        if (!self.uoms_prices_by_product_tmpl_id[item.product_tmpl_id[0]]) {
                            self.uoms_prices_by_product_tmpl_id[item.product_tmpl_id[0]] = [item]
                        } else {
                            self.uoms_prices_by_product_tmpl_id[item.product_tmpl_id[0]].push(item)
                        }
                    }
                }
            }
        }
    ]);

    screens.OrderWidget.include({
        update_summary: function () {
            this._super();
            var selected_order = this.pos.get_order();
            if (selected_order) {
                var buttons = this.getParent().action_buttons;
                if (selected_order && selected_order.selected_orderline) {
                    var is_multi_unit = selected_order.selected_orderline.is_multi_unit_of_measure();
                    if (buttons && buttons.button_choice_uom) {
                        buttons.button_choice_uom.highlight(is_multi_unit);
                    }
                }
            }
        }
    })
});