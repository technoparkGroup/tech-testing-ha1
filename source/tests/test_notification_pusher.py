# coding=utf-8
from argparse import Namespace
import unittest

import tarantool
import mock
from tarantool_queue import Queue
from gevent import queue as gevent_queue

from source import notification_pusher
from source.lib.utils import Config
from source.tests import helpers


class Object():
    def __init__(self):
        pass
    def __call__(self, *args, **kwargs):
        pass


def stop_running(*args):
    notification_pusher.run_application = False


class NotificationPusherTestCase(unittest.TestCase):

    def setUp(self):
        notification_pusher.run_application = True
        self.config = helpers.create_config()
        notification_pusher.sleep = mock.Mock(side_effect=stop_running)

    def test_mainloop_correct_config(self):
        """
        Корректный конфиг
        """

        with mock.patch('gevent.queue.Queue', mock.Mock("create_queue")) as create_queue:
            create_queue.side_effect = stop_running
            notification_pusher.main_loop(config=self.config)
        create_queue.assert_called_once_with()

    @mock.patch('gevent.queue.Queue', mock.Mock("create_queue"))
    def test_mainloop_incorrect_config(self):
        """
        Некорректный конфиг
        """
        self.config.QUEUE_PORT = None
        with self.assertRaises(Queue.BadConfigException):
            notification_pusher.main_loop(config=self.config)

    @mock.patch('source.notification_pusher.done_with_processed_tasks', mock.Mock())
    def test_mainloop_no_free_workers(self):
        """
        Без свободных воркеров
        """
        with mock.patch('source.notification_pusher.get_free_count', mock.Mock(return_value=0)):
            with mock.patch('source.notification_pusher.take_task', mock.Mock()) as take_task:
                notification_pusher.main_loop(self.config)
        assert take_task.not_called

    @mock.patch('source.notification_pusher.done_with_processed_tasks', mock.Mock())
    def test_mainloop_without_tasks(self):
        """
        Со свободными воркерами, но без задач
        """
        task = None
        self.config.WORKER_POOL_SIZE = 1
        with mock.patch('source.notification_pusher.create_worker', mock.Mock()) as create_worker:
            with mock.patch('source.notification_pusher.take_task', mock.Mock(return_value=task)):
                notification_pusher.main_loop(self.config)
        assert create_worker.not_called

    @mock.patch('source.notification_pusher.done_with_processed_tasks', mock.Mock())
    def test_mainloop_with_task(self):
        """
        С задачей
        """
        task = mock.Mock("Task")
        self.config.WORKER_POOL_SIZE = 1
        with mock.patch('source.notification_pusher.create_worker', mock.Mock()) as create_worker:
            with mock.patch('source.notification_pusher.take_task', mock.Mock(return_value=task)):
                notification_pusher.main_loop(self.config)
        assert task in create_worker.call_args[0]

    @mock.patch('source.notification_pusher.done_with_processed_tasks', mock.Mock())
    @mock.patch('source.notification_pusher.take_task', mock.Mock())
    def test_mainloop_start_correct_worker(self):
        """
        Проверяем, что стартуется именно созданный воркер
        """
        self.config.WORKER_POOL_SIZE = 1
        with mock.patch('source.notification_pusher.create_worker', mock.Mock()) as worker:
            notification_pusher.main_loop(self.config)
        assert mock.call().start() in worker.mock_calls

    @mock.patch('source.notification_pusher.done_with_processed_tasks', mock.Mock())
    @mock.patch('source.notification_pusher.take_task', mock.Mock())
    @mock.patch('source.notification_pusher.get_free_count', mock.Mock(return_value=1))
    def test_mainloop_adding_correct_worker_to_workerpool(self):
        """
        Проверяем, что в пул добавляется нужный воркер
        """
        worker = mock.Mock()
        with mock.patch('source.notification_pusher.Pool', mock.Mock()) as worker_pool:
            with mock.patch('source.notification_pusher.create_worker', mock.Mock(return_value=worker)):
                notification_pusher.main_loop(self.config)
        assert mock.call().add(worker) in worker_pool.mock_calls

    def test_done_with_processed_task_call_with_correct_queue(self):
        """
        Проверяем, что на вход метода обработки завершенных задач передается именно созданная в начале очередь
        """
        self.config.WORKER_POOL_SIZE = 0
        processed_queue = mock.Mock()
        with mock.patch('gevent.queue.Queue', mock.Mock(return_value=processed_queue)):
            with mock.patch('source.notification_pusher.done_with_processed_tasks', mock.Mock()) as done:
                notification_pusher.main_loop(self.config)
        done.assert_called_once_with(processed_queue)

    @mock.patch('source.notification_pusher.get_task_queue_size', mock.Mock(return_value=1))
    def test_done_with_processed_tasks_empty_queue(self):
        """
        Пустая очередь
        """
        task_queue = gevent_queue.Queue()
        logger = mock.Mock()
        with mock.patch('source.notification_pusher.logger', logger):
            notification_pusher.done_with_processed_tasks(task_queue)
        empty_msg = notification_pusher.empty_queue_msg
        assert mock.call.debug(empty_msg) in logger.mock_calls

    def test_done_with_processed_tasks_with_task_with_attr(self):
        """
        Все хорошо
        """
        task = Object()
        action_name = "action"
        setattr(task, action_name, Object())

        task_queue = gevent_queue.Queue()
        task_queue.put((task, action_name))
        logger = mock.MagicMock()
        with mock.patch('source.notification_pusher.logger', logger):
            notification_pusher.done_with_processed_tasks(task_queue)
        assert logger.exception.call_count is 0

    def test_done_with_processed_tasks_with_task_without_attr(self):
        """
        Не удалось вызвать getattr у задачи
        """
        task = mock.MagicMock
        action_name = "action"
        task_queue = gevent_queue.Queue()
        task_queue.put((task, action_name))
        logger = mock.Mock()
        e = tarantool.DatabaseError("Error")
        with mock.patch('source.notification_pusher.get_task_attr', mock.Mock(side_effect=e)):
            with mock.patch('source.notification_pusher.logger', logger):
                notification_pusher.done_with_processed_tasks(task_queue)

        assert mock.call.exception(e) in logger.method_calls

    @mock.patch('source.notification_pusher.parse_cmd_args',
                mock.Mock(return_value=Namespace(daemon=True, pidfile=None,
                                                 config='./source/tests/config/pusher_config.py')))
    @mock.patch('source.notification_pusher.main_loop', mock.Mock(side_effect=stop_running))
    @mock.patch('source.notification_pusher.patch_all', mock.Mock())
    def test_main_with_daemon_arg_no_exception(self):
        """
        Проверка вызова метода daemonize при передаче параметра
        Main_loop не выдает эксепшена

        :return:
        """
        with mock.patch('source.notification_pusher.daemonize', mock.Mock()) as daemonize, mock.patch(
                'source.notification_pusher.create_pidfile', mock.Mock()) as create_pidfile, mock.patch(
                'source.notification_pusher.load_config_from_pyfile', mock.Mock(return_value=self.config)):
            notification_pusher.main([])
            daemonize.assert_called_once_with()
            self.assertFalse(create_pidfile.called)
            assert notification_pusher.main_loop.assert_called_once(self.config)

    @mock.patch('source.notification_pusher.parse_cmd_args',
                mock.Mock(return_value=Namespace(daemon=False, pidfile="SomePid",
                                                 config='./source/tests/config/pusher_config.py')))
    @mock.patch('source.notification_pusher.patch_all', mock.Mock())
    @mock.patch('source.notification_pusher.main_loop', mock.Mock(side_effect=Exception('some exc')))
    def test_main_with_create_pidfile_arg_raise_exception(self):
        """
        Проверка вызова метода create_pidfile при передаче параметра
        Exception в main_loop

        :return:
        """
        with mock.patch('source.notification_pusher.daemonize', mock.Mock()) as daemonize, mock.patch(
                'source.notification_pusher.create_pidfile', mock.Mock()) as create_pidfile, mock.patch(
                'source.notification_pusher.load_config_from_pyfile', mock.Mock(return_value=self.config)):
            notification_pusher.main([])
            create_pidfile.assert_called_once_with("SomePid")
            self.assertFalse(daemonize.called)
            assert notification_pusher.main_loop.assert_called_once(self.config)
            assert notification_pusher.sleep.called
pass


