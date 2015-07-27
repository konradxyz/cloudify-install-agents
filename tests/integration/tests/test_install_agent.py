import json
import logging
import os
import shutil
import tempfile
import uuid

import unittest2 as unittest
import yaml

from cloudify.celery import celery
from cloudify.mocks import MockCloudifyContext
from cloudify.state import current_ctx
from cloudify.utils import setup_logger, LocalCommandRunner

import cloudify_agent.installer.config.configuration as agent_config


_SCRIPT_NAME = 'cloudify_install_agents/install_agent.py'
_AGENT_CONFIG = 'agent.json'


def with_agent(f):
    def wrapper(self):
        agent = self.get_agent()
        try:
            f(self, agent)
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
        self.config['repo_dir'] = os.path.expanduser(self.config['repo_dir'])
        self.logger.info(str(self.config))
        current_ctx.set(MockCloudifyContext())
        self.runner = LocalCommandRunner(self.logger)
        self.base_dir = tempfile.mkdtemp()

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
        _, agent_file_path = tempfile.mkstemp()
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
            os.path.join(self.config['repo_dir'], _SCRIPT_NAME),
            operation,
            agent_config_path)
        self.runner.run(command)


class SingleWorkerInstallerTest(InstallerTestBase):

    @with_agent
    def test_installer(self, agent):
        worker_name = 'celery@{0}'.format(agent['name'])
        inspect = celery.control.inspect(destination=[worker_name])
        self.assertFalse(inspect.active())
        self.call('install', agent)
        self.assertTrue(inspect.active())
        self.logger.info(inspect.registered())
        self.call('uninstall', agent)
        self.assertFalse(inspect.active())
