# coding=utf-8
from mock import patch, call
from mock import Mock
from tarantool_queue.tarantool_queue import Tube
import unittest
from source.lib import worker
from source.tests import helpers

class Object():
    def __init__(self):
        pass
    def __call__(self, *args, **kwargs):
        pass
    def __setitem__(self, key, value):
        pass
    def __getitem__(self, item):
        pass

class WorkerTestCase(unittest.TestCase):
    def setUp(self):
        self.config = helpers.create_checker_config()
        self.parent_pid = 1

    @patch('os.path.exists', Mock(return_value=False))
    def test_worker_dead_parent(self):
        """
        Процесса-родителя не существует, не заходим в цикл
        :return:
        """
        input_tube = Mock(name="input_tube")
        input_tube.opt = Object()
        output_tube = Mock(name="output_tube")
        output_tube.opt = Object()
        with patch('source.lib.worker.get_tube', Mock(side_effect=[input_tube, output_tube])):
            worker.worker(self.config, self.parent_pid)
            assert input_tube.called is False

    @patch('os.path.exists', Mock(side_effect=[True, False]))
    @patch.object(Tube, 'take', Mock(return_value=None))
    def test_worker_parent_exists_no_tasks(self):
        """
        Родитель существует, но нет задач, заходим в цикл, но не заходим в первую ветку
        :return:
        """
        with patch('source.lib.worker.get_redirect_history_from_task',
                   Mock(name="get_redirect_history")) as redirect_history:
            worker.worker(self.config, self.parent_pid)
            assert redirect_history.called is False

    @patch('os.path.exists', Mock(side_effect=[True, False]))
    @patch('source.lib.worker.get_redirect_history_from_task', Mock(return_value=None))
    def test_worker_no_redirect_history(self):
        """
        У задачи нет истории редиректов
        :return:
        """
        task = Mock(name="task")
        with patch.object(Tube, 'take', Mock(return_value=task)):
            with patch('source.lib.worker.logger', Mock(name="logger")) as logger:
                worker.worker(self.config, self.parent_pid)
                assert logger.debug.called is False

pass