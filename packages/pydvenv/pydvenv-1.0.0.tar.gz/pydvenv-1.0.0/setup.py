from pip_setuptools import setup, clean, find_packages, requirements, readme

clean()
setup(
    name='pydvenv',
    version='1.0.0',
    author='Маг Ильяс DOMA (MagIlyasDOMA)',
    author_email='magilyas.doma.09@list.ru',
    url='https://github.com/MagIlyasDOMA/pydvenv',
    description='Creating a directory with a Python virtual environment',
    python_requires='>=3.10',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points=dict(console_scripts=[
        'pydvenv=pydvenv.pydvenv:main'
    ]),
    packages=find_packages(),
    extras_require=dict(dev=requirements('dev_requirements.txt')),
    long_description=readme(),
    long_description_content_type='text/markdown',
)