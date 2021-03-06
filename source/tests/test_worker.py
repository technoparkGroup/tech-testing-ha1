# coding=utf-8
from mock import patch, call, MagicMock
from mock import Mock
from tarantool import DatabaseError
from tarantool_queue.tarantool_queue import Tube
import unittest
from source.lib import worker
from source.tests import helpers

class WorkerTestCase(unittest.TestCase):
    def setUp(self):
        self.config = helpers.create_checker_config()
        self.parent_pid = 1
        self.task = MagicMock(name="task")
        self.task.data = {
            "url": "URL",
            "url_id": 1,
            "recheck": False,
        }

    @patch('os.path.exists', Mock(return_value=False))
    def test_worker_dead_parent(self):
        """
        Процесса-родителя не существует, не заходим в цикл
        :return:
        """
        input_tube = MagicMock(name="input_tube")
        output_tube = MagicMock(name="output_tube")
        with patch('source.lib.worker.get_tube', Mock(side_effect=[input_tube, output_tube])):
            worker.worker(self.config, self.parent_pid)
            self.assertFalse(input_tube.called)

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
            self.assertFalse(redirect_history.called)

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
                self.assertFalse(logger.debug.called)

    @patch('os.path.exists', Mock(side_effect=[True, False]))
    def test_worker_is_input_false(self):
        """
        is_input = False
        :return:
        """
        task = Mock(name="task")
        result = (False, "data")
        input_tube = MagicMock(name="input_tube")
        input_tube.take.return_value = task
        output_tube = MagicMock(name="output_tube")
        with patch('source.lib.worker.get_tube', Mock(side_effect=[input_tube, output_tube])):
            with patch('source.lib.worker.get_redirect_history_from_task', Mock(return_value=result)):
                worker.worker(self.config, self.parent_pid)
                output_tube.put.assert_called_once_with("data")

    @patch('os.path.exists', Mock(side_effect=[True, False]))
    def test_worker_is_input_true(self):
        """
        is_input = True
        :return:
        """
        task = MagicMock(name="task")
        result = (True, "data")
        input_tube = MagicMock(name="input_tube")
        input_tube.take.return_value = task
        output_tube = MagicMock(name="output_tube")
        with patch('source.lib.worker.get_tube', Mock(side_effect=[input_tube, output_tube])):
            with patch('source.lib.worker.get_redirect_history_from_task', Mock(return_value=result)):
                worker.worker(self.config, self.parent_pid)
                assert 'data' in input_tube.put.call_args[0]

    @patch('os.path.exists', Mock(side_effect=[True, False]))
    @patch('source.lib.worker.get_redirect_history_from_task', Mock(return_value=None))
    def test_worker_task_ack_exc(self):
        """
        Не удалось выполнить task.ack
        :return:
        """
        task = MagicMock(name="task")
        task.ack.side_effect = DatabaseError
        input_tube = MagicMock(name="input_tube")
        input_tube.take.return_value = task
        output_tube = MagicMock(name="output_tube")
        logger = MagicMock(name="logger")
        with patch('source.lib.worker.get_tube', Mock(side_effect=[input_tube, output_tube])):
            with patch('source.lib.worker.logger', logger):
                worker.worker(self.config, self.parent_pid)
                self.assertTrue(logger.exception.called)

    @patch('os.path.exists', Mock(side_effect=[True, False]))
    @patch('source.lib.worker.get_redirect_history_from_task', Mock(return_value=None))
    def test_worker_task_ack_ok(self):
        """
        Удалось выполнить task.ack
        :return:
        """
        task = MagicMock(name="task")
        input_tube = MagicMock(name="input_tube")
        input_tube.take.return_value = task
        output_tube = MagicMock(name="output_tube")
        logger = MagicMock(name="logger")
        with patch('source.lib.worker.get_tube', Mock(side_effect=[input_tube, output_tube])):
            with patch('source.lib.worker.logger', logger):
                worker.worker(self.config, self.parent_pid)
                self.assertFalse(logger.exception.called)

    @patch('source.lib.worker.get_redirect_history',
           Mock(return_value=([worker.history_type_error], ["URL"], 1)))
    def test_get_redirect_history_from_task_history_error(self):
        """
        Ошибка в истории
        :return:
        """
        result = worker.get_redirect_history_from_task(self.task, 1)
        self.assertEquals(result[1], self.task.data)

    @patch('source.lib.worker.get_redirect_history',
           Mock(return_value=([], ["URL"], 1)))
    def test_get_redirect_history_from_task_history_ok(self):
        """
        Нет ошибок в истории
        :return:
        """
        result = worker.get_redirect_history_from_task(self.task, 1)
        self.assertNotEquals(result[1], self.task.data)

    @patch('source.lib.worker.get_redirect_history',
           Mock(return_value=([], ["URL"], 1)))
    def test_get_redirect_history_from_task_history_ok_with_suspicious(self):
        """
        В данных есть suspicious
        :return:
        """
        task = MagicMock(name="task")
        task.data = {
            "url": "URL",
            "url_id": 1,
            "recheck": False,
            "suspicious": "suspicious"
        }
        result = worker.get_redirect_history_from_task(task, 1)
        self.assertEquals(result[1]["suspicious"], "suspicious")

    @patch('source.lib.worker.get_redirect_history',
           Mock(return_value=([], ["URL"], 1)))
    def test_get_redirect_history_from_task_history_ok_without_suspicious(self):
        """
        Без suspicious в data
        :return:
        """
        result = worker.get_redirect_history_from_task(self.task, 1)
        assert not result[1].has_key("suspicious")
pass