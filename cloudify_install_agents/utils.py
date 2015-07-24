import os


def prepare_script(agent, script_path, dest_path):
    agent_repr = repr(agent)
    in_script = open(script_path).read()
    out_script = in_script.replace('__AGENT_DESCRIPTION__', agent_repr)
    with open(dest_path, 'w') as out_file:
        out_file.write(out_script)
