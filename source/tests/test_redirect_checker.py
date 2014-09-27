# coding=utf-8
from argparse import Namespace
import unittest
import mock
from source import redirect_checker


class RedirectCheckerTestCase(unittest.TestCase):
    def test_main_with_daemon_arg(self):
        """
        Проверка вызова метода daemonize при передаче параметра
        :return:
        """
        redirect_checker.parse_cmd_args = mock.Mock(return_value=Namespace(daemon=True, pidfile=None, config='./source/tests/config/pusher_config.py'))
        daemonize = mock.Mock()
        redirect_checker.daemonize = daemonize
        redirect_checker.main([])
        daemonize.assert_called_once_with()

    def test_main_with_pidfile(self):
        """
        Проверка вызова метода create_pidfile при передаче параметров
        :return:
        """

        parse_cmd_args = mock.Mock()
        pid = "someFile"
        parse_cmd_args.return_value = \
            Namespace(daemon=False, pidfile=pid, config='./source/tests/config/pusher_config.py')
        create_pidfile = mock.Mock()
        redirect_checker.create_pidfile = create_pidfile
        redirect_checker.parse_cmd_args = parse_cmd_args
        redirect_checker.main([])
        create_pidfile.assert_called_once_with(pid)

    pass
