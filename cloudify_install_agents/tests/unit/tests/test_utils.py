import tests.utils as test_utils


class UtilsTest(test_utils.InstallAgentModuleTest):

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
        module = self.import_install_module(agent)
        returned_agent = module.get_cloudify_agent()
        self.assertEquals(agent, returned_agent)
