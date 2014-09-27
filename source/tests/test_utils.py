# coding=utf-8
import os
import unittest
import mock
from source.lib import utils
from source.lib.utils import create_pidfile

class UtilsTestCase(unittest.TestCase):
    def test_create_pidfile_successful(self):
        pid = 42
        m_open = mock.mock_open()
        with mock.patch('source.lib.utils.open', m_open, create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                create_pidfile('/file/path')

        m_open.assert_called_once_with('/file/path', 'w')
        m_open().write.assert_called_once_with(str(pid))

    def test_bad_config_file(self):
        """
        Проверка неправильного пути конфига
        :return:
        """
        # TODO ПОДУМАТЬ
        with self.assertRaises(IOError):
            utils.load_config_from_pyfile("bla-bla")

    def test_correct_config(self):
        """
        Проверка конфига с правильными названиями параметров
        :return:
        """
        # TODO ПОДУМАТЬ
        conf = utils.load_config_from_pyfile(
            os.path.realpath(os.path.expanduser("source/tests/config/test_correct_config.py")))
        self.assertIsNotNone(conf.__getattribute__("QUEUE_HOST"), conf.__getattribute__("QUEUE_PORT"))

    def test_incorrect_config(self):
        """
        Проверка конфига с неверным названием параметра
        :return:
        """
        # TODO ПОДУМАТЬ
        conf = utils.load_config_from_pyfile(
            os.path.realpath(os.path.expanduser("source/tests/config/test_incorrect_config.py")))
        with self.assertRaises(AttributeError):
            conf.__getattribute__("QUEUE_HOST")
pass