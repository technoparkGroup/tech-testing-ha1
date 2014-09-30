# coding=utf-8
from argparse import Namespace
from gevent.pool import Pool
import requests
from tarantool_queue.tarantool_queue import Tube
import unittest

import tarantool
import mock
from tarantool_queue import Queue
from mock import patch
from gevent import queue as gevent_queue, Greenlet

from source import notification_pusher
from source.tests import helpers


def stop_running(*args):
    notification_pusher.run_application = False


class NotificationPusherTestCase(unittest.TestCase):

    def setUp(self):
        notification_pusher.run_application = True
        self.config = helpers.create_pusher_config()
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
        self.config.WORKER_POOL_SIZE = 0
        with patch.object(Tube, 'take', mock.Mock()) as take_task:
            notification_pusher.main_loop(self.config)
        assert take_task.called is False

    @mock.patch('source.notification_pusher.done_with_processed_tasks', mock.Mock())
    def test_mainloop_without_tasks(self):
        """
        Со свободными воркерами, но без задач
        """
        task = None
        self.config.WORKER_POOL_SIZE = 1
        with patch('source.notification_pusher.Greenlet', mock.Mock()) as create_worker:
            with patch.object(Tube, 'take', mock.Mock(return_value=task)):
                notification_pusher.main_loop(self.config)
        assert create_worker.called is False

    @mock.patch('source.notification_pusher.done_with_processed_tasks', mock.Mock())
    def test_mainloop_with_task(self):
        """
        С задачей
        """
        task = mock.Mock(name="Task")
        self.config.WORKER_POOL_SIZE = 1
        with patch('source.notification_pusher.Greenlet', mock.Mock()) as create_worker:
            with patch.object(Tube, 'take', mock.Mock(return_value=task)):
                notification_pusher.main_loop(self.config)
                assert task in create_worker.call_args[0]

    @mock.patch('source.notification_pusher.done_with_processed_tasks', mock.Mock())
    @patch.object(Tube, 'take', mock.Mock())
    def test_mainloop_start_correct_worker(self):
        """
        Проверяем, что стартуется именно созданный воркер
        """
        self.config.WORKER_POOL_SIZE = 1
        worker = mock.Mock()
        with patch('source.notification_pusher.Greenlet', mock.Mock(return_value=worker)):
            notification_pusher.main_loop(self.config)
        assert mock.call.start() in worker.mock_calls

    @mock.patch('source.notification_pusher.done_with_processed_tasks', mock.Mock())
    @patch.object(Tube, 'take', mock.Mock())
    def test_mainloop_adding_correct_worker_to_workerpool(self):
        """
        Проверяем, что в пул добавляется нужный воркер
        """
        worker = mock.Mock()
        worker_pool = mock.Mock()
        with mock.patch('source.notification_pusher.Pool', mock.Mock(return_value=worker_pool)):
            worker_pool.free_count = mock.Mock(return_value=1)
            with patch('source.notification_pusher.Greenlet', mock.Mock(return_value=worker)):
                notification_pusher.main_loop(self.config)
        assert mock.call.add(worker) in worker_pool.mock_calls

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

    @patch.object(gevent_queue.Queue, 'qsize', mock.Mock(return_value=1))
    @patch.object(gevent_queue.Queue, 'get_nowait', mock.Mock(side_effect=gevent_queue.Empty))
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
        task = mock.MagicMock(name="task")
        task_queue = gevent_queue.Queue()
        task_queue.put((task, "action"))
        logger = mock.MagicMock()
        with mock.patch('source.notification_pusher.logger', logger):
            notification_pusher.done_with_processed_tasks(task_queue)
        assert logger.exception.call_count is 0

    def test_done_with_processed_tasks_with_task_without_attr(self):
        """
        Не удалось вызвать getattr у задачи
        """
        task = mock.MagicMock(name="task")
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
                mock.Mock(return_value=Namespace(daemon=False, pidfile=None,
                                                 config='./source/tests/config/pusher_config.py')))
    @mock.patch('source.notification_pusher.patch_all', mock.Mock())
    def test_main_without_args(self):
        """
        в параметрах не передается daemon и pidfile
        :return:
        """
        notification_pusher.run_application = False
        with mock.patch('source.notification_pusher.daemonize', mock.Mock()) as daemonize, mock.patch(
                'source.notification_pusher.create_pidfile', mock.Mock()) as create_pidfile:
            notification_pusher.main([])
            assert not daemonize.called
            assert not create_pidfile.called



    @mock.patch('source.notification_pusher.parse_cmd_args',
                mock.Mock(return_value=Namespace(daemon=True, pidfile=None,
                                                 config='./source/tests/config/pusher_config.py')))
    @mock.patch('source.notification_pusher.patch_all', mock.Mock())
    def test_main_with_daemon_arg(self):
        """
        Проверка вызова метода daemonize при передаче параметра
        :return:
        """
        notification_pusher.run_application = False
        with mock.patch('source.notification_pusher.daemonize', mock.Mock()) as daemonize:
            notification_pusher.main([])
            daemonize.assert_called_once()


    @mock.patch('source.notification_pusher.parse_cmd_args',
                mock.Mock(return_value=Namespace(daemon=False, pidfile="SomePid",
                                                 config='./source/tests/config/pusher_config.py')))
    @mock.patch('source.notification_pusher.patch_all', mock.Mock())
    def test_main_with_create_pidfile_arg(self):
        """
        Проверка вызова метода create_pidfile при передаче параметра

        :return:
        """
        notification_pusher.run_application = False
        with mock.patch('source.notification_pusher.create_pidfile', mock.Mock()) as create_pidfile:
            notification_pusher.main([])
            create_pidfile.assert_called_once_with("SomePid")


    @mock.patch('source.notification_pusher.parse_cmd_args',
                mock.Mock(return_value=Namespace(daemon=False, pidfile=None,
                                                 config='./source/tests/config/pusher_config.py')))
    @mock.patch('source.notification_pusher.main_loop', mock.Mock(side_effect=stop_running))
    @mock.patch('source.notification_pusher.patch_all', mock.Mock())
    def test_main_main_loop_success(self):
        """
        проверка выполнения mainloop без exception

        :return:
        """

        with mock.patch('source.notification_pusher.load_config_from_pyfile', mock.Mock(return_value=self.config)):
            notification_pusher.main([])
            notification_pusher.main_loop.assert_called_once_with(self.config)


    @mock.patch('source.notification_pusher.parse_cmd_args',
                mock.Mock(return_value=Namespace(daemon=False, pidfile=None,
                                                 config='./source/tests/config/pusher_config.py')))
    @mock.patch('source.notification_pusher.main_loop', mock.Mock(side_effect=Exception("some exc")))
    @mock.patch('source.notification_pusher.patch_all', mock.Mock())
    def test_main_main_loop_exception(self):
        """
        проверка выполнения mainloop с exception

        :return:
        """

        with mock.patch('source.notification_pusher.load_config_from_pyfile', mock.Mock(return_value=self.config)):
            notification_pusher.main([])
            assert notification_pusher.sleep.called


    def test_notification_worker_ack(self):
        """
        Если запрос прошел успешно, задача выполнена
        :return:
        """
        task = mock.MagicMock(name="task")
        task_queue = mock.MagicMock(name="task_queue")
        response = mock.MagicMock(name="response")
        with patch('source.notification_pusher.post_request', mock.Mock(return_value=response)):
            notification_pusher.notification_worker(task, task_queue)
        task_queue.put.assert_called_once_with((task, notification_pusher.task_ack))

    def test_notification_worker_bury(self):
        """
        Запрос успешно не прошел
        :return:
        """
        task = mock.MagicMock(name="task")
        task_queue = mock.MagicMock(name="task_queue")
        response = requests.RequestException
        with patch('source.notification_pusher.post_request', mock.Mock(side_effect=response)):
            notification_pusher.notification_worker(task, task_queue)
        task_queue.put.assert_called_once_with((task, notification_pusher.task_bury))

    def test_stop_handler_app_stops(self):
        signal = 100
        notification_pusher.stop_handler(signal)
        assert notification_pusher.run_application is False

    def test_stop_handler_correct_exit_code(self):
        signal = 100
        notification_pusher.stop_handler(signal)
        assert notification_pusher.exit_code is notification_pusher.SIGNAL_EXIT_CODE_OFFSET + signal
pass


