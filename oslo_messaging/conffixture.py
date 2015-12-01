
# Copyright 2013 Red Hat, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

__all__ = ['ConfFixture']

import sys

import fixtures
from functools import wraps


def _import_opts(conf, module, opts, group=None):
    __import__(module)
    conf.register_opts(getattr(sys.modules[module], opts), group=group)


class ConfFixture(fixtures.Fixture):

    """Tweak configuration options for unit testing.

    oslo.messaging registers a number of configuration options, but rather than
    directly referencing those options, users of the API should use this
    interface for querying and overriding certain configuration options.

    An example usage::

        self.messaging_conf = self.useFixture(messaging.ConfFixture(cfg.CONF))
        self.messaging_conf.transport_driver = 'fake'

    :param conf: a ConfigOpts instance
    :type conf: oslo.config.cfg.ConfigOpts
    """

    def __init__(self, conf):
        self.conf = conf
        _import_opts(self.conf,
                     'oslo_messaging._drivers.impl_rabbit', 'rabbit_opts',
                     'oslo_messaging_rabbit')
        _import_opts(self.conf,
                     'oslo_messaging._drivers.amqp', 'amqp_opts',
                     'oslo_messaging_rabbit')
        _import_opts(self.conf,
                     'oslo_messaging._drivers.amqp', 'amqp_opts',
                     'oslo_messaging_qpid')
        _import_opts(self.conf,
                     'oslo_messaging._drivers.protocols.amqp.opts',
                     'amqp1_opts', 'oslo_messaging_amqp')
        _import_opts(self.conf,
                     'oslo_messaging._drivers.impl_zmq', 'zmq_opts')
        _import_opts(self.conf,
                     'oslo_messaging._drivers.zmq_driver.'
                     'matchmaker.matchmaker_redis',
                     'matchmaker_redis_opts',
                     'matchmaker_redis')
        _import_opts(self.conf, 'oslo_messaging.rpc.client', '_client_opts')
        _import_opts(self.conf, 'oslo_messaging.transport', '_transport_opts')
        _import_opts(self.conf,
                     'oslo_messaging.notify.notifier',
                     '_notifier_opts',
                     'oslo_messaging_notifications')

        # Support older test cases that still use the set_override
        # with the old config key names
        def decorator_for_set_override(wrapped_function):
            @wraps(wrapped_function)
            def _wrapper(*args, **kwargs):
                group = 'oslo_messaging_notifications'
                if args[0] == 'notification_driver':
                    args = ('driver', args[1], group)
                elif args[0] == 'notification_transport_url':
                    args = ('transport_url', args[1], group)
                elif args[0] == 'notification_topics':
                    args = ('topics', args[1], group)
                return wrapped_function(*args, **kwargs)
            return _wrapper

        self.conf.set_override = decorator_for_set_override(
            self.conf.set_override)

    def setUp(self):
        super(ConfFixture, self).setUp()
        self.addCleanup(self.conf.reset)

    @property
    def transport_driver(self):
        """The transport driver - for example 'rabbit', 'amqp' or 'fake'."""
        return self.conf.rpc_backend

    @transport_driver.setter
    def transport_driver(self, value):
        self.conf.set_override('rpc_backend', value)

    @property
    def response_timeout(self):
        """Default number of seconds to wait for a response from a call."""
        return self.conf.rpc_response_timeout

    @response_timeout.setter
    def response_timeout(self, value):
        self.conf.set_override('rpc_response_timeout', value)
