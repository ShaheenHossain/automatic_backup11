odoo.define('point_of_sale.screens', function (require) {
	"use strict";
	// This file contains the Screens definitions. Screens are the
	// content of the right pane of the pos, containing the main functionalities. 
	//
	// Screens must be defined and named in chrome.js before use.
	//
	// Screens transitions are controlled by the Gui.
	//  gui.set_startup_screen() sets the screen displayed at startup
	//  gui.set_default_screen() sets the screen displayed for new orders
	//  gui.show_screen() shows a screen
	//  gui.back() goes to the previous screen
	//
	// Screen state is saved in the order. When a new order is selected,
	// a screen is displayed based on the state previously saved in the order.
	// this is also done in the Gui with:
	//  gui.show_saved_screen()
	//
	// All screens inherit from ScreenWidget. The only addition from the base widgets
	// are show() and hide() which shows and hides the screen but are also used to 
	// bind and unbind actions on widgets and devices. The gui guarantees
	// that only one screen is shown at the same time and that show() is called after all
	// hide()s
	//
	// Each Screens must be independant from each other, and should have no 
	// persistent state outside the models. Screen state variables are reset at
	// each screen display. A screen can be called with parameters, which are
	// to be used for the duration of the screen only. 

	var PosBaseWidget = require('point_of_sale.BaseWidget');
	var gui = require('point_of_sale.gui');
	var models = require('point_of_sale.models');
	var core = require('web.core');
	var rpc = require('web.rpc');
	var utils = require('web.utils');
	var field_utils = require('web.field_utils');

	var QWeb = core.qweb;
	var _t = core._t;

	var round_pr = utils.round_precision;
	var ReceiptScreenWidget = ScreenWidget.extend({
		template: 'ReceiptScreenWidget',
		show: function () {
			this._super();
			var self = this;

			this.render_change();
			this.render_receipt();
			this.handle_auto_print();
		},
		handle_auto_print: function () {
			if (this.should_auto_print()) {
				this.print();
				if (this.should_close_immediately()) {
					this.click_next();
				}
			} else {
				this.lock_screen(false);
			}
		},
		should_auto_print: function () {
			return this.pos.config.iface_print_auto && !this.pos.get_order()._printed;
		},
		should_close_immediately: function () {
			return this.pos.config.iface_print_via_proxy && this.pos.config.iface_print_skip_screen;
		},
		lock_screen: function (locked) {
			this._locked = locked;
			if (locked) {
				this.$('.next').removeClass('highlight');
			} else {
				this.$('.next').addClass('highlight');
			}
		},
		get_receipt_render_env: function () {
			var order = this.pos.get_order();
			return {
				widget: this,
				pos: this.pos,
				order: order,
				receipt: order.export_for_printing(),
				orderlines: order.get_orderlines(),
				paymentlines: order.get_paymentlines(),
			};
		},
		print_web: function () {
			window.print();
			this.pos.get_order()._printed = true;
		},
		print_xml: function () {
			var receipt = QWeb.render('XmlReceipt', this.get_receipt_render_env());

			this.pos.proxy.print_receipt(receipt);
			this.pos.get_order()._printed = true;
		},
		print: function () {
			var self = this;

			if (!this.pos.config.iface_print_via_proxy) { // browser (html) printing

				// The problem is that in chrome the print() is asynchronous and doesn't
				// execute until all rpc are finished. So it conflicts with the rpc used
				// to send the orders to the backend, and the user is able to go to the next 
				// screen before the printing dialog is opened. The problem is that what's 
				// printed is whatever is in the page when the dialog is opened and not when it's called,
				// and so you end up printing the product list instead of the receipt... 
				//
				// Fixing this would need a re-architecturing
				// of the code to postpone sending of orders after printing.
				//
				// But since the print dialog also blocks the other asynchronous calls, the
				// button enabling in the setTimeout() is blocked until the printing dialog is 
				// closed. But the timeout has to be big enough or else it doesn't work
				// 1 seconds is the same as the default timeout for sending orders and so the dialog
				// should have appeared before the timeout... so yeah that's not ultra reliable. 

				this.lock_screen(true);

				setTimeout(function () {
					self.lock_screen(false);
				}, 1000);

				this.print_web();
			} else {    // proxy (xml) printing
				this.print_xml();
				this.lock_screen(false);
			}
		},
		click_next: function () {
			this.pos.get_order().finalize();
		},
		click_back: function () {
			// Placeholder method for ReceiptScreen extensions that
			// can go back ...
		},
		renderElement: function () {
			var self = this;
			this._super();
			this.$('.next').click(function () {
				if (!self._locked) {
					self.click_next();
				}
			});
			this.$('.back').click(function () {
				if (!self._locked) {
					self.click_back();
				}
			});
			this.$('.button.print').click(function () {
				if (!self._locked) {
					self.print();
				}
			});
		},
		render_change: function () {
			this.$('.change-value').html(this.format_currency(this.pos.get_order().get_change()));
		},
		render_receipt: function () {
			this.$('.pos-receipt-container').html(QWeb.render('PosTicket', this.get_receipt_render_env()));
			console.log('lorem	***************************************************************');
		},
	});
	gui.define_screen({ name: 'receipt', widget: ReceiptScreenWidget });
