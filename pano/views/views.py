from pano.settings import AVAILABLE_SOURCES
import pytz
class Echo(object):
    """An object that implements just the write method of the file-like
    interface.
    """

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


default_context = {'timezones': pytz.common_timezones,
                   'SOURCES': AVAILABLE_SOURCES}
