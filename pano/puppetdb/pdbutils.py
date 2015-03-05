import datetime


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


def json_to_datetime(date):
    """Tranforms a JSON datetime string into a timezone aware datetime
    object with a UTC tzinfo object.

    :param date: The datetime representation.
    :type date: :obj:`string`

    :returns: A timezone aware datetime object.
    :rtype: :class:`datetime.datetime`
    """
    return datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ').replace(
        tzinfo=UTC())


def is_unreported(node_report_timestamp, unreported=2):
    try:
        if node_report_timestamp is None:
            return True
        last_report = json_to_datetime(node_report_timestamp)
        last_report = last_report.replace(tzinfo=None)
        now = datetime.datetime.utcnow()
        unreported_border = now - datetime.timedelta(hours=unreported)
        if last_report < unreported_border:
            return True
    except AttributeError:
        return True
    return False
