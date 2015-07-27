# Function _get_cloudify_agent should be injected:
# def _get_cloudify_agent():
#     return {
#         'ip': '10.0.4.47',
#         'fabric_env': {},
#         'package_url': ('http://10.0.4.46:53229/packages/'
#                         'agents/ubuntu-trusty-agent.tar.gz'),
#         'port': 22,
#         'manager_ip': '10.0.4.46',
#         'distro_codename': 'trusty',
#         'basedir': '/home/vagrant',
#         'process_management': {
#             'name': 'init.d'
#         },
#         'env': {},
#         'system_python': 'python',
#         'min_workers': 0,
#         'envdir': '/home/vagrant/second_host_0f18c_new/env',
#         'distro': 'ubuntu',
#         'workdir': '/home/vagrant/second_host_0f18c_new/work',
#         'max_workers': 5,
#         'user': 'vagrant',
#         'key': '~/.ssh/id_rsa',
#         'password': None,
#         'agent_dir': '/home/vagrant/second_host_0f18c_new',
#         'name': 'second_host_0f18c_new',
#         'windows': False,
#         'local': False,
#         'queue': 'second_host_0f18c_new',
#         'disable_requiretty': True
#     }

import argparse
import copy
import json
import logging
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import urllib


_CLOUDIFY_DAEMON_QUEUE = 'CLOUDIFY_DAEMON_QUEUE'
_CLOUDIFY_DAEMON_EXTRA_ENV = 'CLOUDIFY_DAEMON_EXTRA_ENV'
_CLOUDIFY_DAEMON_INCLUDES = 'CLOUDIFY_AGENT_INCLUDES'
_CLOUDIFY_DAEMON_WORKDIR = 'CLOUDIFY_DAEMON_WORKDIR'
_CLOUDIFY_DAEMON_USER = 'CLOUDIFY_DAEMON_USER'
_CLOUDIFY_DAEMON_PROCESS_MANAGEMENT = 'CLOUDIFY_DAEMON_PROCESS_MANAGEMENT'
_CLOUDIFY_DAEMON_NAME = 'CLOUDIFY_DAEMON_NAME'
_CLOUDIFY_DAEMON_MIN_WORKERS = 'CLOUDIFY_DAEMON_MIN_WORKERS'
_CLOUDIFY_DAEMON_MAX_WORKERS = 'CLOUDIFY_DAEMON_MAX_WORKERS'
_CLOUDIFY_BROKER_URL = 'CLOUDIFY_BROKER_URL'
_CLOUDIFY_MANAGER_IP = 'CLOUDIFY_MANAGER_IP'
_CLOUDIFY_BROKER_IP = 'CLOUDIFY_BROKER_IP'
_CLOUDIFY_BROKER_PORT = 'CLOUDIFY_BROKER_PORT'
_CLOUDIFY_MANAGER_PORT = 'CLOUDIFY_MANAGER_PORT'
_CLOUDIFY_DAEMON_LOG_LEVEL = 'CLOUDIFY_DAEMON_LOG_LEVEL'
_CLOUDIFY_DAEMON_PID_FILE = 'CLOUDIFY_DAEMON_PID_FILE'
_CLOUDIFY_DAEMON_LOG_FILE = 'CLOUDIFY_DAEMON_LOG_FILE'
_CLOUDIFY_DAEMON_HOST = 'CLOUDIFY_DAEMON_HOST'
_CLOUDIFY_DAEMON_DEPLOYMENT_ID = 'CLOUDIFY_DAEMON_DEPLOYMENT_ID'


def get_cloudify_agent():
    # Should replaced with real representation of agent dict.
    return __AGENT_DESCRIPTION__


def _shlex_split(command):
    lex = shlex.shlex(command, posix=True)
    lex.whitespace_split = True
    lex.escape = ''
    return list(lex)


def _stringify_values(dictionary):
    dict_copy = copy.deepcopy(dictionary)
    for key, value in dict_copy.iteritems():
        if isinstance(value, dict):
            dict_copy[key] = _stringify_values(value)
        else:
            dict_copy[key] = str(value)
    return dict_copy


def _purge_none_values(dictionary):
    dict_copy = copy.deepcopy(dictionary)
    for key, value in dictionary.iteritems():
        if dictionary[key] is None:
            del dict_copy[key]
    return dict_copy


class CommandRunner(object):

    def __init__(self, logger):
        self.logger = logger

    def run(self, command, execution_env=None):
        self.logger.debug('run: {0}'.format(command))
        command_env = os.environ.copy()
        command_env.update(execution_env or {})
        p = subprocess.Popen(_shlex_split(command),
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             env=command_env)
        out, err = p.communicate()
        if p.returncode != 0:
            if out:
                out = out.rstrip()
            if err:
                err = err.rstrip()
            self.logger.error('Command {0} failed.'.format(command))
            self.logger.error('Stdout:')
            self.logger.error(out)
            self.logger.error('Stderr:')
            self.logger.error(err)
            raise Exception()

    def download(self, url, destination=None):
        if destination is None:
            fh_num, destination = tempfile.mkstemp()
            os.close(fh_num)
        urllib.urlretrieve(url, destination)
        return destination

    def create_dir(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    def rm_dir(self, directory):
        shutil.rmtree(directory)

    def untar(self, archive, destination, strip=1):
        return self.run('tar xzvf {0} --strip={1} -C {2}'
                        .format(archive, strip, destination))


class Installer(object):

    def __init__(self, logger, runner, cloudify_agent):
        self.logger = logger
        self.runner = runner
        self.cloudify_agent = cloudify_agent

    @property
    def cfy_agent_path(self):
        return '{0}/bin/python {0}/bin/cfy-agent'.format(
            self.cloudify_agent['envdir'])

    def run_agent_command(self, command, execution_env=None):
        command = '{0} {1}'.format(self.cfy_agent_path, command)
        self.runner.run(command, execution_env)

    def run_daemon_command(self, command, execution_env=None):
        return self.run_agent_command(command='daemons {0} --name={1}'
                                      .format(command,
                                              self.cloudify_agent['name']),
                                      execution_env=execution_env)

    def install(self):
        self.create_env()
        self.create()
        self.run_daemon_command('configure')
        self.run_daemon_command('start')

    def uninstall(self):
        self.run_daemon_command('stop')
        self.run_daemon_command('delete')
        self.delete_env()

    def create_env(self):
        package_path = self.runner.download(
            url=self.cloudify_agent['package_url'])
        self.runner.create_dir(self.cloudify_agent['agent_dir'])
        self.runner.untar(package_path, self.cloudify_agent['agent_dir'])
        command = 'configure --relocated-env'
        if self.cloudify_agent.get('disable_requiretty'):
            command = '{0} --disable-requiretty'.format(command)
        self.run_agent_command(command)

    def create(self):
        self.run_daemon_command(command='create {0}'.format(
            self._create_process_management_options()),
            execution_env=self._create_agent_env())

    def delete_env(self):
        self.runner.rm_dir(self.cloudify_agent['agent_dir'])

    def _create_agent_env(self):
        execution_env = {
            _CLOUDIFY_MANAGER_IP: self.cloudify_agent['manager_ip'],
            _CLOUDIFY_DAEMON_QUEUE: self.cloudify_agent['queue'],
            _CLOUDIFY_DAEMON_NAME: self.cloudify_agent['name'],

            _CLOUDIFY_DAEMON_USER: self.cloudify_agent.get('user'),
            _CLOUDIFY_BROKER_IP: self.cloudify_agent.get('broker_ip'),
            _CLOUDIFY_BROKER_PORT: self.cloudify_agent.get('broker_port'),
            _CLOUDIFY_BROKER_URL: self.cloudify_agent.get('broker_url'),
            _CLOUDIFY_MANAGER_PORT: self.cloudify_agent.get('manager_port'),
            _CLOUDIFY_DAEMON_MAX_WORKERS: self.cloudify_agent.get(
                'max_workers'),
            _CLOUDIFY_DAEMON_MIN_WORKERS: self.cloudify_agent.get(
                'min_workers'),
            _CLOUDIFY_DAEMON_PROCESS_MANAGEMENT:
                self.cloudify_agent['process_management']['name'],
            _CLOUDIFY_DAEMON_WORKDIR: self.cloudify_agent['workdir'],

            # Commenting this out for now - I don't know what is it for.
            # _CLOUDIFY_DAEMON_EXTRA_ENV:
            #    self.create_custom_env_file_on_target(
            #        self.cloudify_agent.get('env', {}))
        }

        execution_env = _purge_none_values(execution_env)
        execution_env = _stringify_values(execution_env)
        return execution_env

    def _create_process_management_options(self):
        options = []
        process_management = copy.deepcopy(self.cloudify_agent[
            'process_management'])

        process_management.pop('name')
        for key, value in process_management.iteritems():
            options.append('--{0}={1}'.format(key, value))
        return ' '.join(options)


def _parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--operation')
    parser.add_argument('--config')
    parser.add_argument('--dryrun', action='store_true', default=False)
    return parser


def _parse_args(parser, args):
    # Unkown args mean we are running in script plugin task.
    # So we are not stopping execution.
    result, _ = parser.parse_known_args(args)
    if result.config is None:
        # Make sure that we are able to retrieve agent config.
        get_cloudify_agent()
    return result


def _prepare_cloudify_agent(path):
    if path:
        with open(path) as f:
            return json.load(f)
    else:
        return get_cloudify_agent()


def _setup_logger(name):
    logger_format = '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
    logger = logging.getLogger(name)
    formatter = logging.Formatter(fmt=logger_format,
                                  datefmt='%H:%M:%S')
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


def _perform_operation(operation, installer):
    if not operation:
        operation = 'install'
    operations = {
        'install': installer.install,
        'create_env': installer.create_env,
        'create': installer.create,
        'delete_env': installer.delete_env,
        'uninstall': installer.uninstall
    }
    if operation in operations:
        operations[operation]()
    else:
        installer.run_daemon_command(operation)


def _main(args):
    parser = _parser()
    command = _parse_args(parser, args[1:])
    cloudify_agent = _prepare_cloudify_agent(command.config)
    logger = _setup_logger('installer')
    runner = CommandRunner(logger)
    installer = Installer(logger, runner, cloudify_agent)
    if command.dryrun:
        logger.info('Options: {0}'.format(str(command)))
        logger.info('Agent:')
        logger.info(str(cloudify_agent))
    else:
        _perform_operation(command.operation, installer)


if __name__ == '__main__':
    _main(sys.argv)
