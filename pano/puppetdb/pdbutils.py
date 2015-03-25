import datetime
import queue
from threading import Thread

from pano.puppetdb import puppetdb
import pano.methods.dictfuncs


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


def run_puppetdb_jobs(jobs, threads=6):
    if type(threads) != int:
        threads = 6
    if len(jobs) < threads:
        threads = len(jobs)
    jobs_q = queue.Queue()
    out_q = queue.Queue()

    def db_threaded_requests(i, q):
        while True:
            t_job = q.get()
            t_path = t_job['path']
            t_params = t_job.get('params', {})
            t_verify = t_job.get('verify', False)
            t_api_v = t_job.get('api', 'v3')
            results = puppetdb.api_get(
                path=t_path,
                params=puppetdb.mk_puppetdb_query(t_params),
                api_version=t_api_v,
                verify=t_verify,
            )
            out_q.put({t_job['id']: results})
            q.task_done()

    for i in range(threads):
        worker = Thread(target=db_threaded_requests, args=(i, jobs_q))
        worker.setDaemon(True)
        worker.start()

    for job in jobs:
        jobs_q.put(jobs[job])
    jobs_q.join()
    job_results = {}
    while True:
        try:
            msg = (out_q.get_nowait())
            job_results = dict(
                list(job_results.items()) + list(msg.items()))
        except queue.Empty:
            break

    return job_results


def get_dashboard_items(jobs):
    jobs_q = queue.Queue()
    out_q = queue.Queue()
    threads = 4

    def db_threaded_requests(i, q):
        while True:
            t_job = q.get()
            t_id = t_job['id']
            t_status = t_job['status']
            t_nodes = t_job['all_nodes']
            t_events = t_job['events']
            t_sort = t_job['sort']
            results = pano.methods.dictfuncs.dictstatus(
                t_nodes, t_events, sort=t_sort, get_status=t_status)
            out_q.put({t_id: results})
            q.task_done()

    for i in range(threads):
        worker = Thread(target=db_threaded_requests, args=(i, jobs_q))
        worker.setDaemon(True)
        worker.start()

    for job in jobs:
        jobs_q.put(jobs[job])
    jobs_q.join()
    job_results = {}
    while True:
        try:
            msg = (out_q.get_nowait())
            job_results = dict(
                list(job_results.items()) + list(msg.items()))
        except queue.Empty:
            break

    return job_results
