/**
 * Created by etaklar on 2015-10-03.
 */
function format(t) {
    var e = "<table><tr><th>Environment: </th><td>" + t.environment + "</td></tr><tr><th>Exported: </th><td>" + t.exported + "</td></tr><tr><th>File: </th><td>" + t.file + ":" + t.line + "</td></tr><tr><th>Parameters:</th></tr>", a = t.parameters;
    return $.each(a, function (t, a) {
        e += "<tr>", e += "<td></td>", e += "<td><strong>" + t + ":</strong> " + a + "</td>", e += "<tr>"
    }), e += "</table>"
}

function update_tables() {
    var t = $("#node-1"), e = $("#node-2"), a = $(t).val(), r = $(t).attr("certname"), o = $(e).val(), n = $(e).attr("certname");
    a == r && get_catalogue(a, "with"), o == n && get_catalogue(o, "against")
}

function get_catalogue(t, e) {
    var a = "#compare-" + e + "-table", r = $("#targets a.active").attr("id");
    if ($.fn.dataTable.isDataTable(a)) {
        var o = $(a).DataTable();
        o.destroy(), $(a).empty()
    }
    if ("edges" == r)$(a).DataTable({
        ajax: "/pano/api/catalogue/get/" + t + "?show=edges",
        columnDefs: [{title: "Source Type", targets: 0}, {title: "Source Title", targets: 1}, {
            title: "Relationship",
            targets: 2
        }, {title: "Target Type", targets: 3}, {title: "Target Title", targets: 4}],
        columns: [{data: "source_type"}, {data: "source_title"}, {data: "relationship"}, {data: "target_type"}, {data: "target_title"}],
        order: [[1, "asc"]]
    });
    else if ("resources" == r) {
        var n = $(a).DataTable({
            ajax: "/pano/api/catalogue/get/" + t + "?show=resources",
            columnDefs: [{title: "Title", targets: 0}, {title: "Type", targets: 1}, {title: "Resource", targets: 2}],
            columns: [{data: "title"}, {data: "type"}, {data: "resource"}],
            order: [[0, "asc"]]
        });
        $(a + " tbody").on("click", "tr", function () {
            var t = $(this).closest("tr"), e = n.row(t);
            e.child.isShown() ? (e.child.hide(), t.removeClass("shown")) : "undefined" != typeof e.data() && (e.child(format(e.data())).show(), t.addClass("shown"))
        })
    }
}

function get_saved_catalogues(certname) {
    var backgroundTask = $.Deferred();

    // Build URL
    var url = '../api/catalogue/saved/list/' + certname;

    $.get(url, function (json) {
            var response = $(jQuery(json));
            var cats = response[0]['catalogues'];
            if (cats) {
                console.log("meow!")
            }
            else {
                console.log('woof!')
            }
        })
        .error(function () {
            // do some error handling here like status code != 200...

        });
}

function repeat(pattern, count) {
    // http://stackoverflow.com/questions/202605/repeat-string-javascript
    if (count < 1) return '';
    var result = '';
    while (count > 1) {
        if (count & 1) result += pattern;
        count >>= 1, pattern += pattern;
    }
    return result + pattern;
}

function type(obj) {
    var text = Function.prototype.toString.call(obj.constructor);
    return text.match(/function (.*)\(/)[1]
}

function get_data(node_1, node_2, catalog_type) {
    var backgroundTask = $.Deferred();

    // Build URL
    var url = '../api/catalogue/compare/' + node_1 + '/' + node_2 + '/?show=' + catalog_type;

    $.get(url, function (json) {
            var response = $(jQuery(json));
            var added = response[0]['added_entries'];
            var removed = response[0]['deleted_entries'];
            var changed = response[0]['changed_entries'];

            var added_data = '';
            var changed_data = '';
            var removed_data = '';

            function textGen(text, dType, sType, indent, tBuffer) {
                indent = indent || 0;
                var tBuffer = '';
                if (dType == 'edges') {
                    tBuffer += '<samp">';
                    tBuffer += '<strong>Source: </strong>' + text.source_type + ' -> ' + text.source_title;
                    tBuffer += '<br>';
                    tBuffer += '<strong>Relationship: </strong>' + text.relationship;
                    tBuffer += '<br>';
                    tBuffer += '<strong>Target: </strong>' + text.target_type + ' -> ' + text.target_title;
                    tBuffer += '</samp>';
                }
                else if (dType == 'resources' && indent == 0) {
                    tBuffer += '<samp">';
                    tBuffer += '<strong>Type: </strong>' + text.type;
                    tBuffer += '<br>';
                    tBuffer += '<strong>Title: </strong>' + text.title;
                    tBuffer += '<br>';
                    tBuffer += '<strong>Resource: </strong>' + text.resource;
                    tBuffer += '<br>';
                    if (Object.keys(text.parameters).length > 0) {
                        tBuffer += '<strong>Parameters:</strong>';
                        tBuffer += '<br>';
                        tBuffer += textGen(text.parameters, 'resources', sType, indent + 1)
                    }
                }
                else if (dType == 'resources' && indent >= 1) {
                    var tab = repeat('&nbsp;&nbsp;&nbsp;', indent);
                    for (var key in text) {
                        if (text.hasOwnProperty(key)) {
                            if (type(text[key]) == 'Object') {
                                tBuffer += tab + '<strong>' + key + ':</strong>';
                                tBuffer += '<br>';
                                tBuffer += textGen(text[key], 'resources', sType, indent + 1)
                            }
                            else if (type(text[key]) == 'Array') {
                                tBuffer += tab + '<strong>' + key + ': </strong>' + text[key].join(', ');
                                tBuffer += '<br>';
                            }
                            else {
                                var keyVal = text[key];
                                if (type(keyVal) == 'String') {
                                    keyVal = keyVal.replace(/(?:\r\n|\r|\n)/g, '<br />');
                                }
                                tBuffer += tab + '<strong>' + key + ': </strong>' + keyVal;
                                tBuffer += '<br>';
                            }
                        }
                    }
                }
                return tBuffer
            }

            if (added) {
                added.forEach(function (add) {
                    added_data += '<div class="bs-callout bs-callout-success">';
                    added_data += textGen(add, catalog_type, 'success');
                    added_data += '</div>';
                });
            }
            if (removed) {
                removed.forEach(function (del) {
                    removed_data += '<div class="bs-callout bs-callout-danger">';
                    removed_data += textGen(del, catalog_type, 'danger');
                    removed_data += '</div>';
                });
            }

            // added data into the div
            $("#diff-added").html(added_data);
            $("#diff-removed").html(removed_data);
        })
        .fail(function () {
            var data = '<tr><td colspan="8">Can not connect to PuppetDB.</td></tr>';
            $("#dashboard_nodes").html(data);
        });
    backgroundTask.resolve();
    return backgroundTask;
}

function compare() {
    var diff_div_add_rem = "#diff-div-add-rem";
    var diff_div_change = "#diff-div-change";
    var is_shown = $(diff_div_add_rem).is(':visible') || $(diff_div_change).is(':visible');

    var type = $("#targets a.active").attr("id");
    var node1 = $("#node-1");
    var node2 = $("#node-2");
    var certname_compare = $(node1).attr("certname");
    var certname_against = $(node2).attr("certname");

    if (!is_shown) {
        if (!certname_compare && !certname_against) {
            $("#form-certname1").addClass("has-error");
            $("#form-certname2").addClass("has-error");
            return (0);
        }
        else if (!certname_compare) {
            $("#form-certname1").addClass("has-error");
            return (0)
        }
        else if (!certname_against) {
            $("#form-certname2").addClass("has-error");
            return (0)
        }
        get_data(certname_compare, certname_against, type);

        $(diff_div_add_rem).toggle();
        $(diff_div_change).toggle();
    }
    else {
        $(diff_div_add_rem).toggle();
        $(diff_div_change).toggle();
    }
}

$(document).ready(function () {
    $("#edges").click(function () {
        $(this).addClass("active").siblings().removeClass("active");
        update_tables();
    });
    $("#resources").click(function () {
        $(this).addClass("active").siblings().removeClass("active");
        update_tables();
    });

    var t = $("#node-1");
    var e = $("#node-2");

    $(t).bind("typeahead:select", function (t, e) {
        $("#node-1").attr("certname", e.certname);
        // Get the resources/edges as soon as something is selected
        get_catalogue(e.certname, "with");

        $("#form-certname1").removeClass("has-error");
    });

    $(e).bind("typeahead:select", function (t, e) {
        $("#node-2").attr("certname", e.certname);
        // Get the resources/edges as soon as something is selected
        get_catalogue(e.certname, "against");
        $("#form-certname2").removeClass("has-error");
    });
    var a = new Bloodhound({
        datumTokenizer: Bloodhound.tokenizers.obj.whitespace("certname"),
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        remote: {url: "/pano/api/nodes/search/?search=%QUERY", wildcard: "%QUERY"}
    });
    $(t).typeahead({highlight: !0}, {
        name: "node-1",
        display: "certname",
        source: a
    });
    $(e).typeahead({highlight: !0}, {name: "node-2", display: "certname", source: a});
});
