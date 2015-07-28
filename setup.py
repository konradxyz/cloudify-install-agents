from setuptools import setup


setup(
    name='cloudify-install-agents',
    packages=[
        'cloudify_install_agents'
    ],
    package_data={
        'cloudify_install_agents':
            ['resources/install_agent.py.template']
    }
)
