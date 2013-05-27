from collections import defaultdict
import json
from logging import getLogger

from paste.deploy.converters import asbool
from redis import Redis
from rq import Queue
from rq.job import Job

from adhocracy.model import meta
from adhocracy.model.refs import to_ref, to_entity

log = getLogger(__name__)

LISTENERS = defaultdict(list)


class async(object):
    """
    An decorator that replaces rq's `.enqueue()` method that detects
    if it is running in a worker and takes care to cleanup after the
    job. You should not call `.enqueue() directly.

    Usage::

      >>> @async
      ... def afunc(arg):
      ...     return arg


    When you call the function you get back a :class:`rq.job.Job`
    proxy object (or a :class:`FakeJob` if no queue is available).

      >>> retval = afunc.enqueue('myarg')
      >>> isinstance(retval, Job)
    """
    def __init__(self, func):
        self.func = func

    def enqueue(self, *args, **kwargs):
        '''
        Call this to guarante the function is enqueued.
        Mostly useful in a worker process where the function
        would be executed synchronously.
        '''
        queue = rq_config.queue
        if queue is None:
            return self.fake_job(*args, **kwargs)
        return queue.enqueue(self.func, *args, **kwargs)

    def fake_job(self, *args, **kwargs):
        fake_job = FakeJob()
        fake_job._result = self.func(*args, **kwargs)
        return fake_job

    def __call__(self, *args, **kwargs):
        '''
        Call this with the args and kwargs of the function you want
        to enqueue. It will queue the function and return a Job if
        a queue is available, or call the function synchronously
        and return a FakeJob if not.

        Returns:

        :class:`FakeJob`
          where `.result` will be the return value if *_force_sync*
          is True or we have no configured redis connection.
        :class:`rq.Job`
          if we do asynchronous processing.
        '''

        if rq_config.in_worker:
            try:
                log.debug('exec job from worker: %s, args: %s, kwargs: %s' % (
                    self.func.__name__, str(args), str(kwargs)))
                return self.func(*args, **kwargs)
            except:
                log.exception('exception in async job execution: %s' % (
                    self.func.__name__))
                raise
            finally:
                # cleanup the sqlalchemy session after we run the job
                # from the queue.
                meta.Session.commit()
                meta.Session.remove()
        else:
            job = self.enqueue(*args, **kwargs)
            if isinstance(job, FakeJob):
                log.debug('fake job execution: %s, args: %s, kwargs: %s'
                          % (self.func.__name__, str(args), str(kwargs)))
            else:
                log.debug('enqueuing job: %s, args: %s, kwargs: %s' % (
                    self.func.__name__, str(args), str(kwargs)))
            return job


# --[ Redis configuration ]-------------------------------------------------

# config will be set from adhocracy.config.environment
# when the pylons application is initialized.

rq_config = None


class RQConfig(object):

    in_worker = False

    def __init__(self, async, host, port, queue_name):
        if host and port and queue_name:
            self.host = host
            self.port = int(port)
            self.queue_name = queue_name
            self.use_redis = True
        else:
            self.use_redis = False

            if async:
                log.warn(('You have not configured redis for adhocracy. '
                          'You should. Current configuration values:'
                          'host: %s, port: %s, name: %s') %
                         (host, port, queue_name))

        self.force_sync = not async
        self.connection = self.new_connection()

    def new_connection(self):
        if not self.use_redis:
            return None
        return Redis(host=self.host, port=self.port)

    @property
    def queue(self):
        if not self.use_redis or (not self.in_worker and self.force_sync):
            return None
        return Queue(self.queue_name, connection=self.connection)

    @classmethod
    def setup_from_config(cls, config):
        global rq_config
        rq_config = cls.from_config(config)

    @classmethod
    def from_config(cls, config):
        async = asbool(config.get('adhocracy.background_processing', 'true'))
        host = config.get('adhocracy.redis.host')
        port = config.get('adhocracy.redis.port')
        name = config.get('adhocracy.redis.queue')
        return cls(async, host, port, name)


# --[ async methods ]-------------------------------------------------------

def update_entity(entity, operation):
    entity_ref = to_ref(entity)
    if entity_ref is None:
        return
    data = dict(operation=operation, entity=entity_ref)
    data_json = json.dumps(data)
    return handle_update(data_json)


@async
def handle_update(message):
    data = json.loads(message)
    entity = to_entity(data.get('entity'))
    for (clazz, operation), listeners in LISTENERS.items():
        if operation != data.get('operation') \
           or not isinstance(entity, clazz):
            continue
        for listener in listeners:
            listener(entity)


@async
def minutely():
    from adhocracy.lib import democracy
    democracy.check_adoptions()


@async
def hourly():
    return
    # nothing here yet


@async
def daily():
    return
    from adhocracy.lib import watchlist
    watchlist.clean_stale_watches()


class FakeJob(Job):
    """
    FakeJob is meant to be used in settings where no redis queue is configured.
    It fakes the signature of a rq Job, but is executed synchronously.

    rq could also do synchronous processing by passing `async=False` to the
    `Queue` constructor, but this would still needs a running Redis process,
    thus we implemented our own way to do this.
    """

    _result = None

    def __init__(self):
        """Override constructor in order to not connect to redis"""
        pass
