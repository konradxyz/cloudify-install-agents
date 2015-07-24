import logging
import unittest2 as unittest
from cloudify.utils import setup_logger

from cloudify_install_agents.install_agent import CommandRunner


class TestRunner(unittest.TestCase):

    def setUp(self):
        self.logger = setup_logger('runner',
                                   logger_level=logging.INFO)
        self.runner = CommandRunner(self.logger)

    def test_run(self):
        self.runner.run('echo "test"')
        with self.assertRaises(Exception):
            self.runner.run('random_command_that_should_not_exist')
