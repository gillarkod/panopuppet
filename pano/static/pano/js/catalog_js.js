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
    var a = "#compare-" + e + "-table";
    var r = $("#targets a.active").attr("id");
    if ($.fn.dataTable.isDataTable(a)) {
        var o = $(a).DataTable();
        o.destroy();
        $(a).empty();
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

function get_saved_catalogues(certname, cType) {
    var backgroundTask = $.Deferred();

    // Build URL
    var url = '../api/catalogue/saved/list/' + certname;
    var list = $("#certname-" + cType + "-hash");
    $.get(url, function (json) {
            var response = $(jQuery(json));
            var cats = response[0]['catalogues'];
            if (cats) {
                list.empty();
                list.append(new Option("Latest Catalogue (PuppetDB)", false));
                cats.forEach(function (cat) {

                    list.append(new Option(cat.catalogue_timestamp + " - " + cat.linked_report, cat.catalogue_id));
                    list.prop("disabled", false);
                })
            }
            else {
                list.empty();
                console.log("This shouldn't have happened! Please raise an issue @ Github!", false);
                list.prop("disabled", true);
            }
        })
        .error(function () {
            // do some error handling here like status code != 200...
            list.empty();
            list.append(new Option("No saved catalogues found. Using latest from PuppetDB", false));
            list.prop("disabled", true);
        });
    backgroundTask.resolve();
    return backgroundTask;
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

function get_compare_data(node_1, node1_hash, node_2, node2_hash, catalog_type) {
    var backgroundTask = $.Deferred();

    // Build URL
    var url = '../api/catalogue/compare/' + node_1 + '/' + node_2 + '/?show=' + catalog_type;
    if (node1_hash && node1_hash != "false") {
        url += "&certname1_hash=" + node1_hash;
    }
    if (node2_hash && node2_hash != "false") {
        url += "&certname2_hash=" + node2_hash;
    }

    $.get(url, function (json) {
            var response = $(jQuery(json));
            var added = response[0]['added_entries'];
            var removed = response[0]['deleted_entries'];
            var changed = response[0]['changed_entries'];

            var added_data = '';
            var changed_data = '';
            var removed_data = '';

            function textGen(text, dType, sType, indent) {
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
                    tBuffer += '<strong>File Line: </strong>' + text.file + ':' + text.line;
                    tBuffer += '<br>';
                    tBuffer += '<strong>Exported: </strong>' + text.exported;
                    tBuffer += '<br>';
                    tBuffer += '<strong>Tags: </strong>' + text.tags;
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

            if (changed) {
                changed.forEach(function (change) {
                    // From data
                    changed_data += '<div class="row">';
                    changed_data += '<div class="col-md-12">';
                    changed_data += '<div class="col-md-6">';
                    changed_data += '<div class="row col-margin" id="diff-changed-from" style="word-wrap: break-word;">';
                    changed_data += '<div class="bs-callout bs-callout-info">';
                    changed_data += textGen(change['from'], catalog_type, 'info');
                    changed_data += '</div>';
                    changed_data += '</div>';
                    changed_data += '</div>';

                    // Against data
                    changed_data += '<div class="col-md-6">';
                    changed_data += '<div class="row col-margin" id="diff-changed-to" style="word-wrap: break-word;">';
                    changed_data += '<div class="bs-callout bs-callout-warning">';
                    changed_data += textGen(change['against'], catalog_type, 'warning');
                    changed_data += '</div>';
                    changed_data += '</div>';
                    changed_data += '</div>';
                    changed_data += '</div>';
                    changed_data += '</div>';
                });
            }

            // added data into the div
            $("#diff-added").html(added_data);
            $("#diff-removed").html(removed_data);
            $("#diff-changed").html(changed_data);
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
    var node1_hash = $("#certname-1-hash");
    var node2 = $("#node-2");
    var node2_hash = $("#certname-2-hash");
    var certname_compare = $(node1).attr("certname");
    var certname_compare_hash = node1_hash.val();
    var certname_against = $(node2).attr("certname");
    var certname_against_hash = node2_hash.val();

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
        get_compare_data(certname_compare, certname_compare_hash, certname_against, certname_against_hash, type);

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
    var selected_node_1 = false;
    var selected_node_2 = false;
    var t = $("#node-1");
    var e = $("#node-2");

    $(t).bind("typeahead:select", function (t, e) {
        $("#node-1").attr("certname", e.certname);
        // Get the resources/edges as soon as something is selected
        get_catalogue(e.certname, "with");
        get_saved_catalogues(e.certname, "1");
        $("#form-certname1").removeClass("has-error");
        selected_node_1 = true;
    });
    $(e).bind("typeahead:select", function (t, e) {
        $("#node-2").attr("certname", e.certname);
        // Get the resources/edges as soon as something is selected
        get_catalogue(e.certname, "against");
        get_saved_catalogues(e.certname, "2");
        $("#form-certname2").removeClass("has-error");
        selected_node_2 = true;
    });

    $(t).bind("typeahead:change", function () {
        var list = $("#certname-1-hash");
        setTimeout(function onUserEdit() {
            if (!selected_node_1) {
                list.empty();
                list.prop("disabled", true);
            }
            else {
                selected_node_1 = false
            }
        }, 100);
    });
    $(e).bind("typeahead:change", function () {
        var list = $("#certname-2-hash");
        setTimeout(function onUserEdit() {
            if (!selected_node_2) {
                list.empty();
                list.prop("disabled", true);
            }
            else {
                selected_node_2 = false
            }
        }, 100);

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
