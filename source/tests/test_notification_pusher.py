# coding=utf-8
from argparse import Namespace
import os
import unittest
import mock
from notification_pusher import create_pidfile
from source import notification_pusher


class NotificationPusherTestCase(unittest.TestCase):
    def test_create_pidfile_example(self):
        pid = 42
        m_open = mock.mock_open()
        with mock.patch('notification_pusher.open', m_open, create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                create_pidfile('/file/path')

        m_open.assert_called_once_with('/file/path', 'w')
        m_open().write.assert_called_once_with(str(pid))

    def test_bad_config_file(self):
        """
        Проверка неправильного пути конфига
        :return:
        """
        with self.assertRaises(IOError):
            notification_pusher.load_config_from_pyfile("bla-bla")

    def test_empty_config_file(self):
        """
        Проверка пустого пути в конфиге
        :return:
        """
        with self.assertRaises(IOError):
            notification_pusher.load_config_from_pyfile("")

    def test_correct_config(self):
        """
        Проверка конфига с правильными названиями параметров
        :return:
        """
        conf = notification_pusher.load_config_from_pyfile(
            os.path.realpath(os.path.expanduser("source/tests/config/test_correct_config.py")))
        self.assertIsNotNone(conf.__getattribute__("QUEUE_HOST"), conf.__getattribute__("QUEUE_PORT"))

    def test_incorrect_config(self):
        """
        Проверка конфига с неверным названием параметра
        :return:
        """
        conf = notification_pusher.load_config_from_pyfile(
            os.path.realpath(os.path.expanduser("source/tests/config/test_incorrect_config.py")))
        with self.assertRaises(AttributeError):
            conf.__getattribute__("QUEUE_HOST")

    def test_main_with_daemon_arg(self):
        """
        Проверка вызова метода daemonize при передаче параметра
        :return:
        """
        notification_pusher.run_application = False
        mock_method_daemonize = mock.MagicMock("daemonize")
        mock_method_parse_cmd_args = mock.MagicMock("parse_cmd")
        mock_method_parse_cmd_args.return_value =\
            Namespace(daemon=True, pidfile=None, config='./source/tests/config/pusher_config.py')
        notification_pusher.parse_cmd_args = mock_method_parse_cmd_args
        notification_pusher.daemonize = mock_method_daemonize
        notification_pusher.main(["-d"])
        mock_method_daemonize.assert_any_call()

    # def test_main_with_pidfile(self):
    #     """
    #     Проверка вызова метода create_pidfile при передаче параметров
    #     :return:
    #     """
    #     notification_pusher.run_application = False
    #     mock_method_parse_cmd_args = mock.MagicMock("parse_cmd")
    #     mock_method_parse_cmd_args.return_value =\
    #         Namespace(daemon=False, pidfile="pidfile", config='./source/tests/config/pusher_config.py')
    #     mock_method_create_pidfile = mock.MagicMock("create_pidfile")
    #     notification_pusher.create_pidfile = mock_method_create_pidfile
    #     notification_pusher.parse_cmd_args = mock_method_parse_cmd_args
    #     notification_pusher.main(["-P pidfile"])
    #     mock_method_create_pidfile.assert_any_call()

    def test_main_with_correct_config(self):
        """
        Проверка работы корректного конфига
        :return:
        """
        notification_pusher.run_application = False
        self.assertEquals(
            notification_pusher.main(['-c ./config/pusher_config.py']),
            0
        )



