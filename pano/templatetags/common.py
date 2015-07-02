__author__ = 'etaklar'

from urllib import parse
from django import template
import json

register = template.Library()


@register.filter
def unquote_raw(value):
    return parse.unquote(value)


@register.filter
def get_item(dictionary, key_id):
    """Returns value in dictionary from the key_id.
       Used when you want to get a value from a dictionary key using a variable
       :param dictionary: dict
       :param key_id: string
       :return: value in the dictionary[key_id]
       How to use:
       {{ mydict|get_item:item.NAME }}
    """
    return dictionary.get(key_id)


@register.filter
def query_to_rules(query):
    operators = ['not', 'and', 'or']
    allowed_equality_operators = ['=', '>', '>=', '<', '<=', '~']
    search_equality_operators = {
        '=': 'equal',
        '~': 'regex_match'
    }
    subq_operators = {
        '=': 'puppet_equal',
        '<': 'puppet_l',
        '<=': 'puppet_le',
        '>': 'puppet_g',
        '>=': 'puppet_ge',
        '~': 'puppet_re_match',
    }

    def read_query(data):
        rules = {
            'condition': '',
            'rules': []
        }

        def certname_search(cert_filter):
            contents = dict()
            # Operator
            contents['operator'] = search_equality_operators[cert_filter[0]]
            # ID
            contents['id'] = cert_filter[1]
            # Value
            contents['value'] = cert_filter[2]
            return contents

        def subquery(subq_filter):
            contents = dict()
            contents['value'] = list()
            # ID
            if subq_filter[2][2][0] == "select-facts":
                contents['id'] = 'facts'
            elif subq_filter[2][2][0] == "select-resources":
                contents['id'] = 'resources'
            elif subq_filter[2][2][0] == "select-nodes":
                contents['id'] = 'nodes'
            # Value 1
            contents['value'].append('"' + subq_filter[2][2][1][1][1] + '"')
            # Value 2
            contents['value'].append(subq_filter[2][2][1][1][2])
            # Operator
            contents['operator'] = subq_operators[subq_filter[2][2][1][1][0]]
            return contents

        i = 0
        while i < len(data):
            # Is it an operator?
            if data[i] in operators:
                rules['condition'] = data[i].upper()
            # identify certname search
            if type(data[i]) is list:
                # if its an equality operator its a certname search
                if data[i][0] in allowed_equality_operators:
                    rules['rules'].append(certname_search(data[i]))
                # is it an operator? Start of a new group?
                elif data[i][0] in operators:
                    rules['rules'].append(read_query(data[i]))
                # if its type string "in" then its the start of a sub query!
                elif data[i][0] == "in":
                    rules['rules'].append(subquery(data[i]))
            i += 1
        return rules
    try:
        pdb_query = json.loads(query)
        pdb_parsed = read_query(pdb_query)
    except:
        pdb_parsed = None
    return json.dumps(pdb_parsed)


@register.filter
def get_percentage(value, max_val):
    """Returns value in dictionary from the key_id.
       Used when you want to get a value from a dictionary key using a variable
       :param dictionary: dict
       :param key_id: string
       :return: value in the dictionary[key_id]
       How to use:
       {{ myval|get_percentage:max_value }}
    """
    if max_val == 0:
        return '0'
    return "{0:.0f}".format((value / max_val) * 100)


@register.simple_tag
def get_status_summary(dictionary, certname, state):
    """
    :param dictionary: dictionary holding the statuses
    :param state: state you want to retrieve
    :param certname: name of the node you want to find
    :return: int
    """
    try:
        return dictionary[certname][state]
    except:
        return 0


@register.filter
def get_bool_status_summary(dictionary, certname, state):
    """
    :param dictionary: dictionary holding the statuses
    :param state: state you want to retrieve
    :param certname: name of the node you want to find
    :return: int
    """
    try:
        if dictionary[certname][state] > 0:
            return True
        else:
            return False
    except:
        return False


class RangeNode(template.Node):
    def __init__(self, range_args, context_name):
        self.range_args = range_args
        self.context_name = context_name

    def render(self, context):
        context[self.context_name] = range(*self.range_args)
        return ""


@register.filter
def colorizediff(content):
    color_diff = []

    for line in content:
        if line.startswith(' '):
            # Nothing has changed
            color_diff.append('<br>' + line.rstrip('\n'))
        elif line.startswith('-'):
            # Line has been removed
            color_diff.append('<br>' + '<span style="color:red">' + line.rstrip('\n') + '</span>')
        elif line.startswith('+'):
            # Line has been added
            color_diff.append('<br>' + '<span style="color:green">' + line.rstrip('\n') + '</span>')
        else:
            color_diff.append('<br>' + line.rstrip('\n'))
    return ''.join(color_diff)


@register.filter
def get_range(value):
    """
      Filter - returns a list containing range made from given value
      Usage (in template):

      <ul>{% for i in 3|get_range %}
        <li>{{ i }}. Do something</li>
      {% endfor %}</ul>

      Results with the HTML:
      <ul>
        <li>0. Do something</li>
        <li>1. Do something</li>
        <li>2. Do something</li>
      </ul>

      Instead of 3 one may use the variable set in the views
    """
    return range(int(value))


@register.filter
def rmDecimal(float_num):
    return "{0:.0f}".format(float_num)


@register.filter
def decimal_to_point(float_num):
    return str(float_num).replace(',', '.')


@register.tag
def mkrange(parser, token):
    """
    Accepts the same arguments as the 'range' builtin and creates
    a list containing the result of 'range'.

    Syntax:
        {% mkrange [start,] stop[, step] as context_name %}

    For example:
        {% mkrange 5 10 2 as some_range %}
        {% for i in some_range %}
          {{ i }}: Something I want to repeat\n
        {% endfor %}

    Produces:
        5: Something I want to repeat
        7: Something I want to repeat
        9: Something I want to repeat
    """

    tokens = token.split_contents()
    fnctl = tokens.pop(0)

    def error():
        raise template.TemplateSyntaxError(fnctl + "accepts the syntax: {%%" + fnctl +
                                           " [start,] stop[, step] as context_name %%}," +
                                           " where 'start', 'stop' and 'step' must all be integers.")

    range_args = []
    while True:
        if len(tokens) < 2:
            error()

        token = tokens.pop(0)

        if token == "as":
            break

        if not token.isdigit():
            error()
        range_args.append(int(token))

    if len(tokens) != 1:
        error()

    context_name = tokens.pop()

    return RangeNode(range_args, context_name)
