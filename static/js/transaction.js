(function (window) {
    'use strict';

    function def_lib() {
        var transaction = {};
        transaction.addto = {tr: null, data: null};

        var row_template = "<tr><td>__name__</td><td class='td-num'>__amount__</td><td class='td-num'>" +
            "__price__</td><td class='td-num'><button class='edit' /><button class='delete' /></td></tr>";

        var row_noprice_template = "<tr><td>__name__</td><td class='td-num'>__amount__</td>" +
            "<td class='td-num'><button class='edit' /><button class='delete' /></td></tr>";

        var deletebutton = "<span class=\"glyphicon glyphicon-remove\" aria-hidden=\"true\"></span>";
        var editbutton = "<span class=\"glyphicon glyphicon-edit\" aria-hidden=\"true\"></span>";

        var preview_normal = "<li role='presentation'><a>_preview_</a></li>";
        var preview_active = "<li role='presentation' class='active'><a>_preview_</a></li>";


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

        transaction.make = function (type) {
            var tr = {
                type: type,
                htmltable: $("#" + type + "-table"),
                datatable: [],
                input_product: $("#" + type + "-product-input"),
                input_amount: $("#" + type + "-amount-input"),
                input_price: $("#" + type + "-price-input")
            };

            tr.data_to_html = function (data) {
                tr.datatable.push(data);

                var str;

                if (tr.type === 'service') {
                    str = row_template;
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
