# coding=utf-8
from argparse import Namespace
import unittest

import mock
from tarantool_queue import Queue

from source import notification_pusher
from source.tests import helpers


class Object():
    def __init__(self):
        pass


class NotificationPusherTestCase(unittest.TestCase):
    def setUp(self):
        notification_pusher.is_testing = True
        notification_pusher.run_application = False

    def test_mainloop_correct_config(self):
        config = helpers.create_config()
        with mock.patch('source.notification_pusher.create_queue', mock.Mock("create_queue")) as create_queue:
            notification_pusher.main_loop(config=config)
        create_queue.assert_called_once_with()

    @mock.patch('source.notification_pusher.create_queue', mock.Mock("create_queue"))
    def test_mainloop_incorrect_config(self):
        config = helpers.create_config()
        config.QUEUE_PORT = None
        with self.assertRaises(Queue.BadConfigException):
            notification_pusher.main_loop(config=config)

    @mock.patch('source.notification_pusher.done_with_processed_tasks', mock.Mock())
    @mock.patch('source.notification_pusher.sleep', mock.Mock())
    def test_mainloop_no_free_workers(self):
        notification_pusher.run_application = True
        with mock.patch('source.notification_pusher.get_free_count', mock.Mock(return_value=0)):
            with mock.patch('source.notification_pusher.take_task', mock.Mock()) as take_task:
                config = helpers.create_config()
                notification_pusher.main_loop(config)
        assert take_task.not_called

    @mock.patch('source.notification_pusher.done_with_processed_tasks', mock.Mock())
    @mock.patch('source.notification_pusher.sleep', mock.Mock())
    def test_mainloop_without_tasks(self):
        notification_pusher.run_application = True
        task = None
        config = helpers.create_config()
        config.WORKER_POOL_SIZE = 1
        with mock.patch('source.notification_pusher.create_worker', mock.Mock()) as create_worker:
            with mock.patch('source.notification_pusher.take_task', mock.Mock(return_value=task)):
                notification_pusher.main_loop(config)
        assert create_worker.not_called

    @mock.patch('source.notification_pusher.done_with_processed_tasks', mock.Mock())
    @mock.patch('source.notification_pusher.sleep', mock.Mock())
    def test_mainloop_with_task(self):
        notification_pusher.run_application = True
        task = mock.Mock("Task")
        config = helpers.create_config()
        config.WORKER_POOL_SIZE = 1
        with mock.patch('source.notification_pusher.create_worker', mock.Mock()) as create_worker:
            with mock.patch('source.notification_pusher.take_task', mock.Mock(return_value=task)):
                notification_pusher.main_loop(config)
        assert task in create_worker.call_args[0]

    @mock.patch('source.notification_pusher.done_with_processed_tasks', mock.Mock())
    @mock.patch('source.notification_pusher.sleep', mock.Mock())
    @mock.patch('source.notification_pusher.take_task', mock.Mock())
    def test_mainloop_start_correct_worker(self):
        notification_pusher.run_application = True
        config = helpers.create_config()
        config.WORKER_POOL_SIZE = 1
        with mock.patch('source.notification_pusher.create_worker', mock.Mock()) as worker:
            notification_pusher.main_loop(config)
        assert mock.call().start() in worker.mock_calls

    @mock.patch('source.notification_pusher.done_with_processed_tasks', mock.Mock())
    @mock.patch('source.notification_pusher.sleep', mock.Mock())
    @mock.patch('source.notification_pusher.take_task', mock.Mock())
    @mock.patch('source.notification_pusher.get_free_count', mock.Mock(return_value=1))
    def test_mainloop_adding_correct_worker_to_workerpool(self):
        notification_pusher.run_application = True
        config = helpers.create_config()
        worker = mock.Mock()
        with mock.patch('source.notification_pusher.Pool', mock.Mock()) as worker_pool:
            with mock.patch('source.notification_pusher.create_worker', mock.Mock(return_value=worker)):
                notification_pusher.main_loop(config)
        assert mock.call().add(worker) in worker_pool.mock_calls

    @mock.patch('source.notification_pusher.sleep', mock.Mock())
    def test_done_with_processed_task_call_with_correct_queue(self):
        notification_pusher.run_application = True
        config = helpers.create_config()
        config.WORKER_POOL_SIZE = 0
        processed_queue = mock.Mock()
        with mock.patch('source.notification_pusher.create_queue', mock.Mock(return_value=processed_queue)):
            with mock.patch('source.notification_pusher.done_with_processed_tasks', mock.Mock()) as done:
                notification_pusher.main_loop(config)
        done.assert_called_once_with(processed_queue)

        # def setUp(self):
        # self.config = mock.Mock()
        #     self.tube = mock.Mock()
        #     self.processed_task_queue = mock.Mock()
        #     self.worker_pool = mock.Mock()
        #     self.queue = mock.Mock()
        #     self.queue.tube.return_value = self.tube
        #     self.parse_cmd_args = mock.Mock()
        #
        # def test_main_with_daemon_arg(self):
        #     """
        #     Проверка вызова метода daemonize при передаче параметра
        #     :return:
        #     """
        #     notification_pusher.run_application = False
        #     self.parse_cmd_args.return_value = Namespace(daemon=True, pidfile=None,
        #                                                  config='./source/tests/config/pusher_config.py')
        #     notification_pusher.parse_cmd_args = self.parse_cmd_args
        #     daemonize = mock.Mock()
        #     notification_pusher.daemonize = daemonize
        #     notification_pusher.main([])
        #     daemonize.assert_called_once_with()
        #
        # def test_main_with_pidfile(self):
        #     """
        #     Проверка вызова метода create_pidfile при передаче параметров
        #     :return:
        #     """
        #
        #     notification_pusher.run_application = False
        #     pid = "someFile"
        #     self.parse_cmd_args.return_value = \
        #         Namespace(daemon=False, pidfile=pid, config='./source/tests/config/pusher_config.py')
        #     create_pidfile = mock.Mock()
        #     notification_pusher.create_pidfile = create_pidfile
        #     notification_pusher.parse_cmd_args = self.parse_cmd_args
        #     notification_pusher.main([])
        #     create_pidfile.assert_called_once_with(pid)
        #
        # def test_mainloop_empty_workerpool(self):
        #     notification_pusher.gevent_queue.Queue = mock.Mock(return_value=self.processed_task_queue)
        #     notification_pusher.tarantool_queue.Queue = mock.Mock(return_value=self.queue)
        #     notification_pusher.Pool = mock.Mock(return_value=self.worker_pool)
        #
        #     notification_pusher.run_application = True
        #     self.worker_pool.free_count.return_value = 0
        #     notification_pusher.done_with_processed_tasks = mock.Mock(return_value=None)
        #     notification_pusher.is_testing = True
        #     notification_pusher.main_loop(config=self.config)
        #     self.assertFalse(self.tube.take.called)
        #
        # def test_mainloop_correct_config(self):
        #     config = helpers.create_config()
        #
        #     create_queue = mock.Mock()
        #     notification_pusher.create_queue = create_queue
        #
        #     notification_pusher.main_loop(config=config)
        #     create_queue.assert_called_once_with()
        #
        # def test_mainloop_incorrect_config(self):
        #     config = helpers.create_config()
        #     config.port = 80
        #     create_queue = mock.Mock()
        #     notification_pusher.create_queue = create_queue
        #
        #     notification_pusher.main_loop(config=config)
        #     create_queue.assert_called_once_with()


pass


