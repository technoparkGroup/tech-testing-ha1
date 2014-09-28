# coding=utf-8
from argparse import Namespace
import unittest
import mock
from source import redirect_checker


class RedirectCheckerTestCase(unittest.TestCase):
    def setUp(self):
        redirect_checker.is_testing = True
        self.config = mock.Mock("mock config")
        self.load_from_pyfile = mock.Mock("mock loader")
        redirect_checker.load_config_from_pyfile = self.load_from_pyfile
        self.load_from_pyfile.return_value=self.config
        self.config.EXIT_CODE = 0
        self.config.SLEEP = 0.1
        self.config.LOGGING = {
            "version" : 1
        }

    @mock.patch('source.redirect_checker.main_loop', mock.Mock())
    @mock.patch('source.redirect_checker.parse_cmd_args', mock.Mock(return_value=Namespace(daemon=True, pidfile=None, config='./source/tests/config/pusher_config.py')))
    def test_main_with_daemon_arg_without_pidfile(self):
        """
        Проверка вызова метода daemonize при передаче параметра
        :return:
        """
        with mock.patch('source.redirect_checker.daemonize', mock.Mock("daemonize mock")) as daemonize:
            with mock.patch('source.redirect_checker.create_pidfile', mock.Mock()) as create_pid:
                self.assertEqual(redirect_checker.main([]), self.config.EXIT_CODE)
                assert create_pid.not_called
                daemonize.assert_called_once_with()
                redirect_checker.main_loop.assert_called_once_with(self.config)


    @mock.patch('source.redirect_checker.main_loop', mock.Mock())
    @mock.patch('source.redirect_checker.parse_cmd_args', mock.Mock(return_value=Namespace(daemon=False, pidfile="somePID", config='./source/tests/config/pusher_config.py')))
    def test_main_with_pidfile_without_daemon(self):
        """
        Проверка вызова метода create_pidfile при передаче параметров
        :return:
        """
        with mock.patch('source.redirect_checker.daemonize', mock.Mock("daemonize mock")) as daemonize:
            with mock.patch('source.redirect_checker.create_pidfile', mock.Mock()) as create_pid:
                self.assertEqual(redirect_checker.main([]), self.config.EXIT_CODE)
                self.assertFalse(daemonize.called)
                create_pid.assert_called_once_with("somePID")
                redirect_checker.main_loop.assert_called_once_with(self.config)

    @mock.patch('source.redirect_checker.check_network_status', mock.Mock(return_value=False))
    @mock.patch('source.redirect_checker.sleep', mock.Mock())
    def test_redirect_checker_mainloop_network_is_down(self):
        """
        тестирование основного цикла с выключенной сетью
        :return:
        """
        my_active_child = mock.Mock()
        with mock.patch('source.redirect_checker.active_children', mock.Mock(return_value=[my_active_child])):
            self.config.SLEEP = 0
            self.config.WORKER_POOL_SIZE = 10
            self.config.CHECK_URL = ''
            self.config.HTTP_TIMEOUT = 1
            redirect_checker.main_loop(self.config)
            assert my_active_child.terminate.called
            assert redirect_checker.sleep.called


    @mock.patch('source.redirect_checker.check_network_status', mock.Mock(return_value=True))
    @mock.patch('source.redirect_checker.sleep', mock.Mock())
    @mock.patch('source.redirect_checker.active_children', mock.Mock(return_value=["some active child"]))
    def test_redirect_checker_mainloop_network_is_up_required_worker_0(self):
        """
        тестирование основного цикла с выключенной сетью
        :return:
        """
        with mock.patch('source.redirect_checker.spawn_workers', mock.Mock()) as spawn_worwkers:
            self.config.SLEEP = 0
            self.config.WORKER_POOL_SIZE = 1
            self.config.CHECK_URL = ''
            self.config.HTTP_TIMEOUT = 1
            redirect_checker.main_loop(self.config)
            assert redirect_checker.sleep.called
            assert spawn_worwkers.not_called

    @mock.patch('source.redirect_checker.check_network_status', mock.Mock(return_value=True))
    @mock.patch('source.redirect_checker.sleep', mock.Mock())
    @mock.patch('source.redirect_checker.active_children', mock.Mock(return_value=["some active child"]))
    def test_redirect_checker_mainloop_network_is_up_required_worker_not_0(self):
        """
        тестирование основного цикла с выключенной сетью
        :return:
        """
        pid = 123
        with mock.patch('os.getpid', mock.Mock(return_value=pid)):
            with mock.patch('source.redirect_checker.spawn_workers', mock.Mock()) as spawn_worwkers:
                self.config.SLEEP = 0
                self.config.WORKER_POOL_SIZE = 2
                required_workers_count = self.config.WORKER_POOL_SIZE - len(redirect_checker.active_children())
                self.config.CHECK_URL = ''
                self.config.HTTP_TIMEOUT = 1
                redirect_checker.main_loop(self.config)
                assert redirect_checker.sleep.called
                spawn_worwkers.assert_called_once()
                num = spawn_worwkers.call_args[1]['num']
                parent_id = spawn_worwkers.call_args[1]['parent_pid']
                assert num == required_workers_count
                assert pid == parent_id

    pass
