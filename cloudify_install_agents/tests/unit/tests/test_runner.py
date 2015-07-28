import tests.utils as test_utils


class TestRunner(test_utils.InstallAgentModuleTest):

    def setUp(self):
        super(TestRunner, self).setUp()
        self.runner = self.install_agent.CommandRunner(self.logger)

    def test_run(self):
        self.runner.run('echo "test"')
        with self.assertRaises(Exception):
            self.runner.run('random_command_that_should_not_exist')
