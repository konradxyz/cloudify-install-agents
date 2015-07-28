import importlib
import os
import shutil
import sys
import tempfile

import unittest2 as unittest

from cloudify.utils import setup_logger

import cloudify_install_agents.utils as utils


class InstallAgentModuleTest(unittest.TestCase):
    def setUp(self):
        self.logger = setup_logger('InstallAgentModuleTest')
        self.dest_path = tempfile.mkdtemp()
        self.install_agent = self.import_install_module({})

    def import_install_module(self, agent):
        _, dest_script = tempfile.mkstemp(suffix='.py', dir=self.dest_path)
        utils.prepare_script(agent, dest_script)
        name, _ = os.path.splitext(os.path.basename(dest_script))
        sys.path.append(self.dest_path)
        return importlib.import_module(name)

    def tearDown(self):
        shutil.rmtree(self.dest_path)
