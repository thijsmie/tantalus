/// IMP functionality

var posting = false;

function post_object(object, endpoint, redirect) {
    if (posting)
        return;
    posting = true;

    console.log(JSON.stringify(object));
    $.ajax({
        type: "POST",
        url: endpoint,
        data: JSON.stringify(object),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (data) {
            window.location.href = redirect;
        },
        error: function (data) {
            posting = false;
            display_errors(data);
        }
    });
}

function display_errors(data) {
    for (var i = 0; i < data.responseJSON['messages'].length; i++) {
        var msg = data.responseJSON['messages'][i];
        display_error(msg);
    }
}

function display_error(message) {
    $("#messages").append($("<div />", {
        "class": "alert alert-danger alert-dismissable", role: "alert", html:
        '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>'
        + message
    }));
}

function valid_integer(val) {
    var intRegex = /^-?\d+$/;
    if (!intRegex.test(val))
        return false;

    var intVal = parseInt(val, 10);
    return parseFloat(val) == intVal && !isNaN(intVal);
}

function valid_float(val) {
    var floatRegex = /^-?\d+(?:[.,]\d*?)?$/;
    if (!floatRegex.test(val))
        return false;

    val = parseFloat(val);
    if (isNaN(val))
        return false;
    return true;
}

String.prototype.capitalize = function () {
    return this.charAt(0).toUpperCase() + this.slice(1);
};

function field_validate_int(field) {
    if (!valid_integer($(field).val())) {
        display_error(field.capitalize() + ": '" + $(field).val() + "' is not a valid integer.");
        return false;
    }
    return true;
}

function field_validate_int_or_none(field) {
    if ($(field).val() == '')
        return true;
    return field_validate_int(field);
}

function field_validate_float(field) {
    if (!valid_float($(field).val())) {
        display_error(field.capitalize() + ": '" + $(field).val() + "' is not a valid float.");
        return false;
    }
    return true;
}

function field_validate_strlen(field, length) {
    if ($(field).val().length < length) {
        display_error(field.capitalize() + ": '" + $(field).val() + "' is not at least length " + length + ".");
        return false;
    }
    return true;
}

function field_validate_float_or_none(field) {
    if ($(field).val() == '')
        return true;
    return field_validate_float(field);
}

function field_validate_money(field) {
    const re = /^(-?\d+)((?:[\.,]\d{0,2})?)$/u;
    let data = $(field).val();
    let m = re.exec(data);
    if (m === null) {
        display_error(field.capitalize() + ": '" + data + "' is not a valid amount of money.");
        return false;
    }
    return true;
}

function field_validate_money_or_none(field) {
    if ($(field).val() == '')
        return true;
    return field_validate_money(field);
}

function parseMoney(val) {
    const re = /^(-?)(\d*)((?:[\.,]\d{0,2})?)$/u;
    let m = re.exec(val);
    if (m === null) {
        display_error(val + "' is not a valid amount of money.");
        return 0;
    }
    let euros = (m[2] === "" ? 0 : parseInt(m[2]));
    var cents = 0;
    if (m[3] !== "" && m[3] !== "." && m[3] !== ",")
      if (m[3].length === 2)
        cents = parseInt(m[3].substring(1)) * 10;
      else
        cents = parseInt(m[3].substring(1));
    return (euros * 100 + cents) * (m[1] === "-" ? -1 : 1);
}

function formatMoney(val) {
    return "" + (val / 100.0).toFixed(2).replace('.', ',');
}