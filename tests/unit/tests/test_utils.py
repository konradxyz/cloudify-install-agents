import sys
import importlib
import os
import tempfile
import unittest2 as unittest
import yaml
import shutil

from cloudify.utils import setup_logger

import cloudify_install_agents.utils as utils


_SCRIPT_NAME = 'cloudify_install_agents/install_agent.py'


class UtilsTest(unittest.TestCase):

    def setUp(self):
        self.logger = setup_logger('UtilsTest')
        config_path = os.environ.get('CONFIG_PATH')
        self.logger.info('Config: {0}'.format(config_path))
        with open(config_path) as config_file:
            self.config = yaml.load(config_file)
        self.config['repo_dir'] = os.path.expanduser(self.config['repo_dir'])
        self.dest_path = tempfile.mkdtemp()
        open(os.path.join(self.dest_path, '__init__.py'), 'a').close()
        self.logger.info('Destination path: {0}'.format(self.dest_path))

    def test_prepare_script(self):
        agent = {
            'ip': '10.0.4.47',
            'fabric_env': {},
            'package_url': ('http://10.0.4.46:53229/packages/'
                            'agents/ubu\'ntu-trusty-agent.tar.gz'),
            'port': 22,
            'manager_ip': '10.0.4.46',
            'distro_codename': 'trusty',
            'basedir': '/home/vagrant',
            'process_management': {
                'name': 'init.d'
            },
            'env': {},
            'system_python': 'python',
            'min_workers': 0,
            'envdir': '/home/vagrant/second_host_0f18c_new/env',
            'distro': 'ubuntu',
            'workdir': '/home/vagrant/second_host_0f18c_new/work',
            'max_workers': 5,
            'user': 'vagrant',
            'key': '~/.ssh/id_rsa',
            'password': None,
            'agent_dir': '/home/vagrant/second_host_0f18c_new',
            'name': 'second_host_0f18c_new',
            'windows': False,
            'local': False,
            'queue': 'second_host_0f18c_new',
            'disable_requiretty': True
        }
        script_path = os.path.join(self.config['repo_dir'], _SCRIPT_NAME)
        module_name = 'temporary_install_agent'
        dest_script = os.path.join(self.dest_path,
                                   '{0}.py'.format(module_name))
        utils.prepare_script(agent, script_path, dest_script)
        sys.path.append(self.dest_path)
        module = importlib.import_module(module_name)
        returned_agent = module.get_cloudify_agent()
        self.assertEquals(agent, returned_agent)

    def tearDown(self):
        shutil.rmtree(self.dest_path)
