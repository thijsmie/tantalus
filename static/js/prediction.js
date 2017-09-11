(function (window) {
    'use strict';

    function def_lib() {
        var prediction = {};
        prediction.make = function (option_list, input_element, output_element, maxlen, preview_element, active_preview_element) {
            var predictor = {
                maxlen: maxlen,
                ctext: "",
                selected: -1,
                selection: [],
                sel_index: 0,
                options: option_list,
                tag_list: [],
                input: input_element,
                output: output_element,
                preview_element: preview_element,
                active_preview_element: active_preview_element
            };

            predictor.findoptions = function (query) {
                var result = [];
                var re = new RegExp(query, 'i');
                if (predictor.tag_list.length > 0) {
                    $.each(predictor.tag_list, function (i, value) {
                        if (value !== "" && value === query)
                            result.push(i);
                    });
                }
                $.each(predictor.options, function (i, value) {
                    if (re.test(value))
                        result.push(i);
                });
                return result.slice(0, predictor.maxlen);
            };

            predictor.perform_selection = function (option) {
                var cl = function () {
                    predictor.selected = option;
                    predictor.finalize();
                };
                return cl;
            };

            predictor.preview = function () {
                var out = predictor.output;
                var active = predictor.sel_index;
                out.empty();
                $.each(predictor.selection, function (i, option) {
                    if (i === active)
                        out.append($(predictor.active_preview_element.replace("_preview_", predictor.options[option]))
                            .click(predictor.perform_selection(option)));
                    else
                        out.append($(predictor.preview_element.replace("_preview_", predictor.options[option]))
                            .click(predictor.perform_selection(option)));
                });
            };

            predictor.textupdate = function () {
                if (predictor.input.val() != predictor.ctext) {
                    predictor.ctext = predictor.input.val();
                    predictor.selection = predictor.findoptions(predictor.ctext);

                    if (predictor.selection.length === 0) {
                        predictor.sel_index = -1;
                        predictor.selected = -1;
                    }
                    else {
                        predictor.selected = predictor.selection[0];
                        predictor.sel_index = 0;
                    }
                    predictor.preview();
                }
            };

            predictor.update = function (e) {
                if (e.which === 13) {
                    e.stopPropagation();
                    e.preventDefault();

                    predictor.finalize()
                }
                else if (e.which === 9) {
                    e.stopPropagation();
                    e.preventDefault();

                    predictor.sel_index = (predictor.sel_index + 1) % predictor.selection.length;
                    predictor.selected = predictor.selection[predictor.sel_index];
                    predictor.preview();
                }
                else {
                    predictor.textupdate();
                }
            };

            predictor.finalize = function () {
                predictor.input.val(predictor.options[predictor.selected]);
                predictor.output.empty();
            };

            predictor.input.data('predictor', predictor);
            predictor.input.keydown(predictor.update);
            predictor.input.keyup(predictor.textupdate);
            predictor.input.focus(function () {
                predictor.ctext = " ";
                predictor.textupdate()
            });
            return predictor;
        };
        return prediction;
    }

    if (typeof(prediction) === "undefined") {
        window.prediction = def_lib();
    }
    else {
        console.log("CRIT (prediction): window.prediction was already defined!");
    }
})(window);