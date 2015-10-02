import datetime

from django import template

__author__ = 'etaklar'

register = template.Library()


# used for json_to_datetime filter
class UTC(datetime.tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return str('UTC')

    def dst(self, dt):
        return datetime.timedelta(0)

    def __repr__(self):
        return str('<UTC>')

    def __str__(self):
        return str('UTC')

    def __unicode__(self):
        return 'UTC'


@register.simple_tag
def dictKeyLookup(the_dict, key):
    # Try to fetch from the dict, and if it's not found return an empty string.
    return the_dict.get(key, '')


@register.filter
def json_to_datetime(date):
    """Tranforms a JSON datetime string into a timezone aware datetime
    object with a UTC tzinfo object.
    :param date: The datetime representation.
    :type date: :obj:`string`
    :returns: A json time stamp converted to readable timestamp in str format
    :rtype: basestring
    """
    try:
        time = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=UTC())
        return time
    except:
        if date is None:
            return 'None'
