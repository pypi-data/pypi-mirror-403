#!/usr/bin/env python3
import argparse, venv, os, subprocess
import sys
from pathlib import Path
from typing import Union
from urllib.parse import urlparse
from . import __version__


class PythonDirectoryVirtualEnvironment:
    def __init__(self):
        self._init_parser()
        self.cwd = Path.cwd()
    
    def _init_parser(self):
        self.parser = argparse.ArgumentParser(description='Creating a directory with a Python virtual environment')
        self.fs_group = self.parser.add_mutually_exclusive_group()
        self.logging_group = self.parser.add_mutually_exclusive_group()
    
        self.parser.add_argument('--version', '-v', action='version', version=__version__)
    
        # Позиционные аргументы как опциональные
        self.parser.add_argument('base_dir', type=str, nargs='?', default=None,
                            help='Base directory to create the virtual environment (default: current directory)')
        self.parser.add_argument('env_name', type=str, nargs='?', default='.venv',
                            help='Name of the virtual environment (default: .venv)')
    
        # Флаг для переопределения имени
        self.parser.add_argument('--env-name', '-e', type=str, dest='env_name_flag',
                            help='Name of the virtual environment (overrides positional argument)')

        self.parser.add_argument('--clear', '--rewrite', '-c', action='store_true',
                            help='Delete the contents of the environment directory if it already exists, before environment creation')
        self.parser.add_argument('--system-site-packages', '--system', '-s', action='store_true',
                            help='Give the virtual environment access to the system site-packages dir',
                            dest='system_site_packages')
        self.fs_group.add_argument('--symlinks', '-S', '-L', action='store_true',
                            help='Try to use symlinks rather than copies, when symlinks are not the default '
                                 'for the platform. May not be supported on Windows.')
        self.fs_group.add_argument('--copies', '-C', action='store_true',
                                   help='Try to use copies rather than symlinks, '
                                        'even when symlinks are the default for the platform')
        self.parser.add_argument('--without-pip', '-P', action='store_false', dest='with_pip',
                            help='Skips installing or upgrading pip in the virtual environment (pip is bootstrapped by default)')
        self.parser.add_argument('--upgrade-deps', '-u', action='store_true',
                            help='Upgrade core dependencies (pip) to the latest version in PyPI')
        self.parser.add_argument('--prompt', '-p', type=str, help='Provides an alternative prompt prefix for this environment')
    
        self.parser.add_argument('--create-git-repository', '--create-git', '--init-git-repository',
                            '--init-git', '-g', action='store_true', dest='create_git_repository',
                            help='Creates a Git repository. The virtual environment folder is automatically added to .gitignore')
        self.parser.add_argument('--return-to-cwd', '-R', action='store_true',
                           help='Return in the current directory')
        self.parser.add_argument('--requirements', '-r', nargs='?', default=None, type=str,
                           const='requirements.txt', action='append', dest='requirements_files',
                           help="Install python packages from the given requirements file. This option can be used multiple times")

        self.logging_group.add_argument('--verbose', '-V', '--logging', '--log', '-l',
                                        action='store_true', help='Enable logging', dest='log_mode')
        self.logging_group.add_argument('--debug-logging', '--debug', '-d', action='store_true',
                                        help='Enable debug logging', dest='debug_mode')

        return self.parser

    def git_init(self):
        if self.create_git_repository:
            result = subprocess.run(['git', 'init'], capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError('Failed to initialize git repository')
            self.log(result.stdout)
            no_gitignore = not os.path.isfile('.gitignore')
            with open('.gitignore', 'a+') as file:
                file.seek(0)
                content = file.read()
                if not any((content.endswith('\n'), no_gitignore)):
                    file.write('\n')
                    self.debug_log('Added \\n letter to .gitignore')
                if self.env_name not in content:
                    file.write(f'{self.env_name}\n')
                    self.log(f'Added {self.env_name} directory to .gitignore')

    @staticmethod
    def is_url(input: str) -> bool:
        parsed = urlparse(str(input))
        return bool(parsed.scheme and parsed.netloc)

    @property
    def env_dir(self):
        return Path.cwd() / self.env_name

    def create_script_path(self, path: Union[str, Path], add_exe_if_windows: bool = False) -> Path:
        is_windows = sys.platform == 'win32'
        base_dir = self.env_dir / 'Scripts' if is_windows else 'bin'
        if add_exe_if_windows and is_windows:
            path = str(path) + '.exe'
        return base_dir / path
    
    def install_requirements(self):
        if self.requirements_files:
            self.debug_log(f'Using requirements files:', ', '.join(self.requirements_files))
            command = f'{str(self.create_script_path("pip", True))} install'
            for requirements_file in self.requirements_files:
                if not self.is_url(requirements_file) and not os.path.isabs(requirements_file):
                    requirements_file = str(self.cwd / requirements_file)
                command += f' -r {requirements_file}'
            if self.debug_mode:
                command += ' -vvv'
            elif not self.log_mode:
                command += ' -q'
            self.debug_log('Running command:', command)
            os.system(command)

    def activate_instructions(self):
        self.log('To activate the python virtual environment, run:', self.create_script_path('activate'))

    def activate(self):
        raise NotImplementedError

    @staticmethod
    def init_symlinks(args):
        if args.symlinks: return True
        elif args.copies: return False
        else: return None

    def _init_args(self, args=None):
        if args is None:
            args = self.parser.parse_args()

        self.base_dir = args.base_dir
        self.env_name = args.env_name_flag or args.env_name
        self.venv_params = dict(
            env_dir=self.env_name,
            system_site_packages=args.system_site_packages,
            clear=args.clear,
            symlinks=self.init_symlinks(args),
            with_pip=args.with_pip,
            upgrade_deps=args.upgrade_deps,
            prompt=args.prompt
        )
        self.create_git_repository = args.create_git_repository
        self.return_to_cwd = args.return_to_cwd
        self.requirements_files = args.requirements_files
        self.log_mode = args.log_mode
        self.debug_mode = args.debug_mode

        if self.venv_params['symlinks'] is None:
            del self.venv_params['symlinks']

    def log(self, *values, sep: str = ' ', end: str = '\n'):
        if self.log_mode:
            print(*values, sep=sep, end=end)

    def debug_log(self, *values, sep: str = ' ', end: str = '\n'):
        if self.debug_mode or self.log_mode:
            print(*values, sep=sep, end=end)
    
    def run(self):
        self._init_args()
    
        # Создаем директорию, если указана и отличается от текущей
        if self.base_dir and self.base_dir not in ('.', self.cwd):
            os.makedirs(self.base_dir, exist_ok=True)
            os.chdir(self.base_dir)
    
        # Создаем виртуальное окружение
        venv.create(**self.venv_params)
        self.log(f'Created python virtual environment in {Path.cwd() / self.env_name}')
    
        self.git_init()
        self.install_requirements()
    
        if self.return_to_cwd:
            os.chdir(self.cwd)
        else:
            self.activate_instructions()


def main(): PythonDirectoryVirtualEnvironment().run()


if __name__ == '__main__':
    main()