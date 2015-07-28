import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
import uuid

import unittest2 as unittest
import yaml
from celery import Celery

from cloudify.celery import celery
from cloudify.mocks import MockCloudifyContext
from cloudify.state import current_ctx
from cloudify.utils import setup_logger, LocalCommandRunner

import cloudify_agent.installer.config.configuration as agent_config

import cloudify_install_agents.utils as install_utils


def with_agent(f):
    def wrapper(self, **kwargs):
        agent = self.get_agent()
        try:
            f(self, agent, **kwargs)
        finally:
            self.cleanup_agent(agent)
    wrapper.__name__ = f.__name__
    return wrapper


class InstallerTestBase(unittest.TestCase):

    def setUp(self):
        self.logger = setup_logger('InstallerTest')
        config_path = os.environ.get('CONFIG_PATH')
        self.logger.info('Config: {0}'.format(config_path))
        with open(config_path) as config_file:
            self.config = yaml.load(config_file)
        self.logger.info(str(self.config))
        current_ctx.set(MockCloudifyContext())
        self.runner = LocalCommandRunner(self.logger)
        self.base_dir = tempfile.mkdtemp()
        self.logger.info('Base dir: {0}'.format(self.base_dir))
        _, self.script_path = tempfile.mkstemp(dir=self.base_dir,
                                               suffix='.py')
        install_utils.prepare_script({}, self.script_path)

    def tearDown(self):
        shutil.rmtree(self.base_dir)

    def get_agent(self):
        result = {
            'local': True,
            'package_url': self.config['agent_url'],
            'user': self.config['agent_user'],
            'basedir': self.base_dir,
            'manager_ip': '127.0.0.1',
            'name': 'agent_{0}'.format(uuid.uuid4())
        }
        agent_config.prepare_connection(result)
        # We specify base_dir and user directly, so runner is not needed.
        agent_config.prepare_agent(result, None)
        _, agent_file_path = tempfile.mkstemp(dir=self.base_dir)
        with open(agent_file_path, 'a') as agent_file:
            agent_file.write(json.dumps(result))
        result['agent_file'] = agent_file_path
        return result

    def cleanup_agent(self, agent):
        os.remove(agent['agent_file'])

    def call(self, operation, agent):
        agent_config_path = agent['agent_file']
        command = '{0} {1} --operation={2} --config={3}'.format(
            self.config['python_path'],
            self.script_path,
            operation,
            agent_config_path)
        self.logger.info('Calling: "{0}"'.format(command))
        self.runner.run(command)


class SingleWorkerInstallerTest(InstallerTestBase):

    @with_agent
    def test_installer(self, agent):
        worker_name = 'celery@{0}'.format(agent['name'])
        inspect = celery.control.inspect(destination=[worker_name])
        self.assertFalse(inspect.active())
        self.call('install', agent)
        self.assertTrue(inspect.active())
        self.call('uninstall', agent)
        self.assertFalse(inspect.active())


class DoubleWorkerInstallerTest(InstallerTestBase):

    def setUp(self):
        super(DoubleWorkerInstallerTest, self).setUp()
        self.server = subprocess.Popen(
            ['python', '-m', 'SimpleHTTPServer', '8000'],
            cwd=self.base_dir)
        # It is not the best way to wait for server to start.
        # However, for now it will be enough.
        time.sleep(1)

    def tearDown(self):
        self.server.kill()
        self.server.communicate()
        super(DoubleWorkerInstallerTest, self).tearDown()

    @with_agent
    def test_double_installer(self, agent):

        @with_agent
        def _double_agents_test(self, agent, parent_agent):
            parent_name = 'celery@{0}'.format(parent_agent['name'])
            inspect = celery.control.inspect(destination=[parent_name])
            self.assertFalse(inspect.active())
            self.call('install', parent_agent)
            self.assertTrue(inspect.active())
            self.logger.info('Agent {0} active.'.format(parent_agent['name']))
            try:
                # Must end with .py:
                installer_name = 'installer.py'
                output = os.path.join(self.base_dir, installer_name)
                install_utils.prepare_script(agent,
                                             output)
                worker_name = 'celery@{0}'.format(agent['name'])
                worker_inspect = celery.control.inspect(
                    destination=[worker_name])
                self.assertFalse(worker_inspect.active())
                celery_app = Celery(broker='amqp://', backend='amqp://')
                self.logger.info('Sending installer task')
                result = celery_app.send_task(
                    'script_runner.tasks.run',
                    args=['http://localhost:8000/{0}'.format(installer_name)],
                    queue=parent_agent['queue'])
                result.get()
                self.assertTrue(worker_inspect.active())
                self.call('uninstall', agent)
                self.assertFalse(worker_inspect.active())
            finally:
                self.call('uninstall', parent_agent)
                self.assertFalse(inspect.active())
        _double_agents_test(self, parent_agent=agent)
