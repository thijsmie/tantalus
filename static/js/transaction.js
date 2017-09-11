(function (window) {
    'use strict';

    function def_lib() {
        var transaction = {};
        transaction.addto = {modcell: null, tr: null, data: null};

        var row_template = "<tr><td>__name__</td><td class='td-num'>__amount__</td><td class='td-num'>__price__</td>" +
            "<td class='modholder'></td><td class='td-num'><span id='modalopen' class='glyphicon glyphicon-plus' aria-hidden='true'" +
            " data-toggle='modal' data-target='#mod-modal'></span><button class='edit' /><button class='delete' /></td></tr>";

        var row_nomods_template = "<tr><td>__name__</td><td class='td-num'>__amount__</td><td class='td-num'>" +
            "__price__</td><td class='td-num'><button class='edit' /><button class='delete' /></td></tr>";

        var row_noprice_template = "<tr><td>__name__</td><td class='td-num'>__amount__</td><td class='modholder'></td>" +
            "<td class='td-num'><span id='modalopen' class='glyphicon glyphicon-plus' aria-hidden='true' data-toggle='modal' " +
            "data-target='#mod-modal'></span><button class='edit' /><button class='delete' /></td></tr>";

        var modtemplate = '<button type="button" class="btn btn-__type__ btn-xs" data-toggle="tooltip" data-placement="top"' +
            ' title="__eq__">tag</button>';
        var deletebutton = "<span class=\"glyphicon glyphicon-remove\" aria-hidden=\"true\"></span>";
        var editbutton = "<span class=\"glyphicon glyphicon-edit\" aria-hidden=\"true\"></span>";

        var preview_normal = "<li role='presentation'><a>_preview_</a></li>";
        var preview_active = "<li role='presentation' class='active'><a>_preview_</a></li>";

        transaction.get_mod_by_id = function (modid) {
            var mod = 0;
            $.each(mods, function (i, imod) {
                if (imod.id === modid)
                    mod = imod;
            });
            return mod;
        };

        transaction.init = function (endp) {
            transaction.endpoint = endp;

            var prnamemap = products.map(function (x) {
                return x['contenttype'];
            });

            var prtagmap = products.map(function (x) {
                return x['tag'];
            });

            var relnamemap = relations.map(function (x) {
                return x['name'];
            });

            var sp = prediction.make(prnamemap, $("#sell-product-input"), $("#sell-preview"), 7, preview_normal, preview_active);
            var bp = prediction.make(prnamemap, $("#buy-product-input"), $("#buy-preview"), 7, preview_normal, preview_active);
            var rp = prediction.make(relnamemap, $("#relation-input"), $("#relation-preview"), 7, preview_normal, preview_active);

            $("#relation-input").keyup(function (e) {
                if (e.which === 13) {
                    $("#delivered").focus();
                }
            });

            sp.tag_list = prtagmap;
            bp.tag_list = prtagmap;

            window.sell_data = transaction.make('sell');
            window.buy_data = transaction.make('buy');
            window.service_data = transaction.make('service');

            $("#mod-modal").find(":button.btn-xs").click(function (e) {
                if ($.inArray($(this).data("id"), transaction.addto.data.mods) === -1) {
                    transaction.addto.modcell.append(transaction.addto.tr.make_mod_button(transaction.get_mod_by_id($(this).data("id")), transaction.addto.data));
                    transaction.addto.data.mods.push($(this).data("id"))
                }
                ;
            });
        };

        transaction.submit = function () {
            var rec = {
                sell: window.sell_data.datatable,
                buy: window.buy_data.datatable,
                service: window.service_data.datatable
            };

            var rel_input = $("#relation-input");
            if (rel_input.data('predictor').selected === -1) {
                display_error("Unmatched relation!");
                return;
            }

            rec.relation = window.relations[rel_input.data('predictor').selected].id;
            rec.description = $("#event").val();
            rec.deliverydate = $("#delivered").val();

            post_object(rec, transaction.endpoint, "/transaction");
        };

        transaction.render_mod_as_equation = function (mod) {
            var left = '', right = '';

            if (mod.rounding !== 'none') {
                left = mod.rounding + '(';
                right = ')';
            }

            if (mod.pre_add !== 0) {
                left += '(€ + ' + transaction.format_currency(mod.pre_add) + ')';
            }
            else {
                left += '€';
            }

            if (mod.divides) {
                left += ' / ';
            }
            else {
                left += ' × ';
            }

            if (mod.multiplier !== 1.0) {
                left += mod.multiplier.toFixed(2);
            }

            if (mod.post_add !== 0) {
                left += ' + ' + transaction.format_currency(mod.post_add);
            }

            return left + right;
        };

        transaction.pad = function (num, size) {
            while (num.length < size) num = "0" + num;
            return num;
        };

        transaction.strip_non_digit = function (string) {
            const regex = /[^\d-]|(^0*)/g;
            return string.replace(regex, "");
        };

        transaction.caret_position = function (elem, caretPos) {
            var range;

            if (elem.createTextRange) {
                range = elem.createTextRange();
                range.move('character', caretPos);
                range.select();
            } else {
                elem.focus();
                if (elem.selectionStart !== undefined) {
                    elem.setSelectionRange(caretPos, caretPos);
                }
            }
        };

        transaction.parse_price = function (string) {
            return parseInt(parseFloat(string.replace(',', '.')) * 100.0);
        };

        transaction.format_currency = function (int) {
            return "" + (int / 100.0).toFixed(2).replace('.', ',');
        };

        transaction.add_mod_me = function (e) {
            console.log($(this).data("id"));
        };

        transaction.make = function (type) {
            var tr = {
                type: type,
                htmltable: $("#" + type + "-table"),
                datatable: [],
                input_product: $("#" + type + "-product-input"),
                input_amount: $("#" + type + "-amount-input"),
                input_price: $("#" + type + "-price-input")
            };

            tr.get_mod_objects = function (mod_ids) {
                var toadd = [];

                $.each(mod_ids, function (i, id) {
                    $.each(mods, function (i, mod) {
                        if (id === mod.id) {
                            toadd.push(mod);
                        }
                    });
                });

                return toadd;
            };

            tr.get_mod_ids = function (product) {
                var tofind = [];
                if (type === "sell") {
                    tofind = product.losemods;
                }
                else if (type === "buy") {
                    tofind = product.gainmods;
                }

                return tofind;
            };

            tr.make_mod_button = function (mod, data) {
                var str = modtemplate;
                str = str.replace('__eq__', transaction.render_mod_as_equation(mod));
                if (mod.modifies)
                    str = str.replace('__type__', "primary");
                else
                    str = str.replace('__type__', "default");
                str = str.replace(/tag/g, mod.tag);

                var button = $(str);
                button.click(function () {
                    tr.modremove(button, mod, data);
                }).tooltip();

                return button;
            };

            tr.modremove = function (button, mod, data) {
                button.remove();
                tr.htmltable.find(".tooltip").remove();
                data.mods = data.mods.filter(function (omod) {
                    return omod !== mod.id;
                });
            };

            tr.data_to_html = function (data) {
                tr.datatable.push(data);

                var str;

                if (tr.type === 'service') {
                    str = row_nomods_template;
                }
                else if (tr.type === 'sell') {
                    str = row_noprice_template;
                }
                else {
                    str = row_template;
                }

                str = str.replace("__name__", data['contenttype']);
                str = str.replace("__amount__", data['amount']);

                if (tr.type !== 'sell')
                    str = str.replace("__price__", transaction.format_currency(data['price']));

                var row = $(str);
                row.find('button.edit').first().replaceWith($(editbutton).click(function () {
                    tr.edit(row, data)
                }));
                row.find('button.delete').first().replaceWith($(deletebutton).click(function () {
                    tr.del(row, data)
                }));

                if (tr.type !== 'service') {
                    var modcell = row.find('td.modholder').first();
                    $.each(tr.get_mod_objects(data.mods), function (i, mod) {
                        modcell.append(tr.make_mod_button(mod, data));
                    });
                    row.find("#modalopen").first().click(function (e) {
                        transaction.addto = {tr: tr, modcell: modcell, data: data};
                    });
                }
                tr.htmltable.append(row);
            };

            tr.fetch_new_row = function () {
                var row = {
                    contenttype: tr.input_product.val(),
                    amount: parseInt(tr.input_amount.val())
                };

                if (tr.type !== 'sell')
                    row.price = transaction.parse_price(tr.input_price.val());

                if (tr.input_product.data('predictor')) {
                    if (tr.input_product.data('predictor').selected === -1) {
                        display_error("A " + tr.type + " product must be selected!");
                        return;
                    }

                    if (tr.type === 'buy' && row.price < 0) {
                        display_error("Can't buy a product with negative price!");
                        return;
                    }

                    if (row.amount < 0) {
                        display_error("A " + tr.type + " product cannot have a negative amount!");
                        return;
                    }

                    var product = products[tr.input_product.data('predictor').selected];
                    row.id = product.id;
                    row.mods = tr.get_mod_ids(product);
                }

                return row;
            };

            tr.edit = function (row, data) {
                tr.del(row, data);
                tr.input_product.val(data['contenttype']);

                tr.input_amount.val(data['amount']);

                if (tr.type !== 'service') {
                    $.each(products, function (i, val) {
                        if (val.id === data['id']) {
                            tr.input_product.data('predictor').selected = i;
                        }
                    });
                }

                if (tr.type !== 'sell')
                    tr.input_price.val(transaction.format_currency(data['price']).replace(',', '.'));
            };

            tr.del = function (row, data) {
                tr.datatable = tr.datatable.filter(function (t) {
                    return t !== data
                });
                row.remove();
            };

            tr.product_input_keydown = function (e) {
                if (e.which === 13) { // Enter
                    e.stopPropagation();
                    e.preventDefault();

                    tr.input_amount.focus();
                }
            };

            tr.amount_input_keyup = function (e) {
                tr.input_amount.val(transaction.strip_non_digit(tr.input_amount.val()));
            };

            tr.amount_input_keydown = function (e) {
                if (e.which === 13 || e.which === 9) {
                    e.stopPropagation();
                    e.preventDefault();

                    if (e.shiftKey) {
                        tr.input_product.focus();
                        return;
                    }

                    if (tr.type === 'sell') {
                        var row = tr.fetch_new_row();

                        if (row) {
                            tr.data_to_html(row);
                            tr.input_product.val("").focus();
                            tr.input_amount.val("");
                        }
                    }
                    else {
                        tr.input_price.focus();
                    }
                }
            };

            tr.price_input_keydown = function (e) {
                if (e.which === 13 || e.which === 9) {
                    e.stopPropagation();
                    e.preventDefault();

                    if (e.shiftKey) {
                        tr.input_amount.focus();
                        return;
                    }

                    var row = tr.fetch_new_row();

                    if (row) {
                        tr.data_to_html(row);
                        tr.input_product.val("").focus();
                        tr.input_amount.val("");
                        tr.input_price.val("0.00");
                    }
                }
                else if (e.which === 65) {
                    tr.input_price.val((parseFloat(tr.input_price.val()) * parseInt(tr.input_amount.val())).toFixed(2));
                }
            };

            tr.price_input_keyup = function (e) {
                var money = transaction.pad(transaction.strip_non_digit(tr.input_price.val()), 3);
                var index = money.length - 2;
                tr.input_price.val(money.substring(0, index) + "." + money.substring(index));
                transaction.caret_position(tr.input_price, tr.input_price.val().length);
            };

            tr.input_product.keydown(tr.product_input_keydown);

            tr.input_amount.keyup(tr.amount_input_keyup);
            tr.input_amount.keydown(tr.amount_input_keydown);

            if (tr.type !== 'sell') {
                tr.input_price.focus(function () {
                    if ($(this).val() === "") $(this).val("0.00");
                });
                tr.input_price.keydown(tr.price_input_keydown);
                tr.input_price.keyup(tr.price_input_keyup);
            }
            return tr;
        };
        return transaction;
    }

    if (typeof(transaction) === "undefined") {
        window.transaction = def_lib();
    }
    else {
        console.log("CRIT (transaction): window.transaction was already defined!");
    }
})(window);