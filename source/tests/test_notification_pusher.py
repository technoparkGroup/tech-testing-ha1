# coding=utf-8
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