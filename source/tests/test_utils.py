# coding=utf-8
from argparse import Namespace
import os
import unittest
import urllib2
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


    @mock.patch('os.getpid', mock.Mock(return_value=42))
    def test_create_pidfile_exception(self):
        m_open = mock.Mock(side_effect=IOError("file not found"))
        with mock.patch('source.lib.utils.open', m_open, create=True):
            with self.assertRaises(IOError):
                create_pidfile('/file/path')
        assert m_open.write.not_called

    def test_bad_config_file(self):
        """
        Проверка неправильного пути конфига
        :return:
        """
        with self.assertRaises(IOError):
            utils.load_config_from_pyfile("bad config path")

    def test_correct_config(self):
        """
        Проверка конфига с правильными названиями параметров
        :return:
        """
        conf = utils.load_config_from_pyfile(
            os.path.realpath(os.path.expanduser("source/tests/config/test_correct_config.py")))
        self.assertIsNotNone(getattr(conf, "QUEUE_HOST"), getattr(conf, "QUEUE_PORT"))

    def test_incorrect_config(self):
        """
        Проверка конфига с неверным названием параметра
        :return:
        """
        conf = utils.load_config_from_pyfile(
            os.path.realpath(os.path.expanduser("source/tests/config/test_incorrect_config.py")))
        with self.assertRaises(AttributeError):
            getattr(conf, "QUEUE_HOST")

    def test_try_fork_successful(self):
        """
        fork выдает pid и не выдает exception
        :return:
        """
        pid = 100
        with mock.patch('os.fork', mock.Mock(return_value=pid)):
            self.assertEqual(utils.try_fork(), pid)

    def test_try_fork_exception(self):
        """
        fork выдает exception
        :return:
        """
        with mock.patch('os.fork', mock.Mock(side_effect=OSError("error"))), self.assertRaises(Exception):
            utils.try_fork()

    @mock.patch('os.setsid', mock.Mock())
    def test_daemonize_pid_0(self):
        """
        pid всегда = 0. os_exit не должен вызываться
        :return:
        """
        with mock.patch('source.lib.utils.try_fork', mock.Mock(return_value=0)):
            with mock.patch('os._exit', mock.Mock()) as exit:
                utils.daemonize()
                assert exit.not_called

    @mock.patch('os.setsid', mock.Mock())
    def test_daemonize_pid_not_0(self):
        """
        pid всегда != 0. os_exit должен вызваться
        :return:
        """
        with mock.patch('source.lib.utils.try_fork', mock.Mock(return_value=100)):
            with mock.patch('os._exit', mock.Mock()) as exit:
                utils.daemonize()
                assert exit.called


    @mock.patch('os.setsid', mock.Mock())
    def test_daemonize_pid_not_0_second_time(self):
        """
        pid всегда = 0 при первом вызове и != 0 при втором. os_exit должен вызваться
        :return:
        """
        with mock.patch('source.lib.utils.try_fork', mock.Mock(side_effect=[0, 1])):
            with mock.patch('os._exit', mock.Mock()) as exit:
                utils.daemonize()
                assert exit.called


    @mock.patch('urllib2.urlopen', mock.Mock())
    def test_check_network_succesfull(self):
        assert utils.check_network_status("someurl", 0)


    @mock.patch('urllib2.urlopen', mock.Mock(side_effect=urllib2.URLError("url exception")))
    def test_check_network_exception(self):
        self.assertFalse(utils.check_network_status("someurl", 10))


    def test_spawn_process_empty(self):
        """
        процессы не создаются
        :return:
        """
        my_process = mock.MagicMock()
        with mock.patch('multiprocessing.Process', mock.Mock(return_value=my_process)):
            utils.spawn_workers(0, "target", args=[], parent_pid=10)
            assert not my_process.start.called


    def test_spawn_process_not_empty(self):
        """
        процессы создаются
        :return:
        """
        my_process = mock.MagicMock()
        call_count = 10
        with mock.patch('source.lib.utils.Process', mock.Mock()) as process:
            utils.spawn_workers(call_count, "target", args=[], parent_pid=10)
            assert process.call_count == call_count

    # def test_parse_cmd_args_without_params(self):
    #     """
    #     нет параметров командной строки, нет обязательного параметра
    #     :return:
    #     """
    #     with self.assertRaises(Exception):
    #         utils.parse_cmd_args([])

    def test_parse_cmd_args_with_params(self):
        """
        нет параметров командной строки, нет обязательного параметра
        :return:
        """
        config_path = 'some path'
        pidfile = "pidfile"
        self.assertEqual(utils.parse_cmd_args(['-c', config_path, '-d', '-P', pidfile]), Namespace(config=config_path, daemon=True, pidfile=pidfile))


pass