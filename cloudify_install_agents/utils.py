import pkg_resources
import os


def prepare_script(agent, dest_path):
    script_path = pkg_resources.resource_filename('cloudify_install_agents',
                                                  'install_agent.py')
    agent_repr = repr(agent)
    in_script = open(script_path).read()
    out_script = in_script.replace('__AGENT_DESCRIPTION__', agent_repr)
    with open(dest_path, 'w') as out_file:
        out_file.write(out_script)
