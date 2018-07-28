import os

from setuptools import setup, find_packages
# To use a consistent encoding
import codecs

here = os.path.abspath(os.path.dirname(__file__))
about = {}

try:
    import pypandoc

    long_description = pypandoc.convert('README.md', 'rst')
except ImportError:
    long_description = codecs.open('README.md').read()

with open(os.path.join(here, 'sewer', '__version__.py'), 'r') as f:
    exec(f.read(), about)

setup(
    name=about['__title__'],
    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=about['__version__'],
    description=about['__description__'],
    long_description=long_description,
    # The project's main homepage.
    url=about['__url__'],
    # Author details
    author=about['__author__'],
    author_email=about['__author_email__'],
    # Choose your license
    license=about['__license__'],
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',
        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Security',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Networking',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    # What does your project relate to?
    keywords='letsencrypt',
    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    # packages=['sewer'],
    packages=find_packages(exclude=['docs', '*tests*']),
    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    #   py_modules=["my_module"],
    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        'requests', 'pyopenssl', 'cryptography', 'tldextract', 'apache-libcloud', 'dnspython'
    ],
    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip3 install -e .[dev,test]
    # TODO: gate auroraDns like we gate aliyunDns
    extras_require={
        'dev': ['coverage', 'pypandoc', 'twine', 'wheel'],
        'test': ['flake8==3.5.0', 'mock', 'pylint==1.8.2', 'pycodestyle==2.3.1'],
        'aliyun': ['aliyun-python-sdk-core-v3', 'aliyun-python-sdk-alidns'],
        'alicloud': ['aliyun-python-sdk-core-v3', 'aliyun-python-sdk-alidns'],
    },
    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    # package_data={
    #     'sample': ['package_data.dat'],
    # },
    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[('my_data', ['data/data_file'])],
    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    # entry_points={
    #     'console_scripts': [
    #         'sample=sample:main',
    #     ],
    # },
    entry_points={
        'console_scripts': [
            'sewer=sewer.cli:main',
            'sewer-cli=sewer.cli:main',
        ],
    },
)

# python packaging documentation:
# 1. https://python-packaging.readthedocs.io/en/latest/index.html
# 2. https://python-packaging-user-guide.readthedocs.io/tutorials/distributing-packages
# a) pip3 install wheel twine
# b) pip3 install -e .
# c) python setup.py sdist
# d) python setup.py bdist_wheel
# e) DONT use python setup.py register and python setup.py upload. They use http
# f) twine upload dist/* -r testpypi
# g) pip3 install -i https://testpypi.python.org/pypi <package name>
# h) twine upload dist/*   # prod pypi
# i) pip3 install <package name>
