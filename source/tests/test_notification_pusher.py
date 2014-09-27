# coding=utf-8
from argparse import Namespace
import unittest

import mock

from source import notification_pusher

class Object():
    pass

class NotificationPusherTestCase(unittest.TestCase):
    def setUp(self):
        self.config = mock.Mock()
        self.tube = mock.Mock()
        self.processed_task_queue = mock.Mock()
        self.worker_pool = mock.Mock()
        self.queue = mock.Mock()
        self.queue.tube.return_value=self.tube
        notification_pusher.gevent_queue.Queue = mock.Mock(return_value=self.processed_task_queue)
        notification_pusher.tarantool_queue.Queue = mock.Mock(return_value=self.queue)
        notification_pusher.Pool = mock.Mock(return_value=self.worker_pool)
        self.parse_cmd_args = mock.Mock()

    def test_main_with_daemon_arg(self):
        """
        Проверка вызова метода daemonize при передаче параметра
        :return:
        """
        notification_pusher.run_application = False
        self.parse_cmd_args.return_value = Namespace(daemon=True, pidfile=None,
                                                     config='./source/tests/config/pusher_config.py')
        notification_pusher.parse_cmd_args = self.parse_cmd_args
        daemonize = mock.Mock()
        notification_pusher.daemonize = daemonize
        notification_pusher.main([])
        daemonize.assert_called_once_with()

    def test_main_with_pidfile(self):
        """
        Проверка вызова метода create_pidfile при передаче параметров
        :return:
        """

        notification_pusher.run_application = False
        pid = "someFile"
        self.parse_cmd_args.return_value = \
            Namespace(daemon=False, pidfile=pid, config='./source/tests/config/pusher_config.py')
        create_pidfile = mock.Mock()
        notification_pusher.create_pidfile = create_pidfile
        notification_pusher.parse_cmd_args = self.parse_cmd_args
        notification_pusher.main([])
        create_pidfile.assert_called_once_with(pid)

    def test_mainloop_empty_workerpool(self):
        notification_pusher.run_application = True
        self.worker_pool.free_count.return_value = 0
        notification_pusher.done_with_processed_tasks = mock.Mock(return_value=None)
        notification_pusher.is_testing = True
        notification_pusher.main_loop(config=self.config)
        self.assertFalse(self.tube.take.called)

    def test_mainloop_not_empty_workerpool(self):
        notification_pusher.run_application = True
        self.worker_pool.free_count.return_value = 5
        notification_pusher.done_with_processed_tasks = mock.Mock(return_value=None)
        notification_pusher.is_testing = True
        task = Object()
        task.task_id = 5
        self.tube.take.return_value = task
        greenlet = mock.Mock()
        notification_pusher.Greenlet = mock.Mock(return_value=greenlet)
        notification_pusher.main_loop(config=self.config)
        self.assertTrue(self.tube.take.called)
        self.worker_pool.assert_called_once_with(greenlet)


pass


