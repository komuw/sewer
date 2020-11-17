import codecs, json, os
from setuptools import setup, find_packages

# long description comes from README.md
with codecs.open("README.md", "r", encoding="utf8") as f:
    long_description = f.read()
ldct = "text/markdown"

# version and other fields in about, with envvar override
with codecs.open(os.path.join("sewer", "meta.json"), "r", encoding="utf8") as f:
    meta = json.load(f)

for k in meta:
    if "SETUP_" + k in os.environ:
        meta[k] = os.environ["SETUP_" + k]

# provider catalog, used to construct the list of extras and their deps, and all their deps
with codecs.open(os.path.join("sewer", "catalog.json"), "r", encoding="utf8") as f:
    catalog = json.load(f)

provider_deps_map = dict((i["name"], i["deps"]) for i in catalog)

all_deps_of_all_providers = list(set(sum((i["deps"] for i in catalog), [])))


setup(
    long_description=long_description,
    long_description_content_type=ldct,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Security",
        "Topic :: System :: Installation/Setup",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    packages=find_packages(exclude=["docs", "*tests*"]),
    install_requires=["requests", "cryptography"],
    extras_require=dict(
        provider_deps_map,
        dev=["twine", "wheel"],
        test=["mypy>=0.780", "coverage>=5.0", "pytest>=6.0", "pylint>=2.6.0", "black==19.10b0"],
        alldns=all_deps_of_all_providers,
    ),
    # data files to be placed in project directory, not zip safe but zips suck anyway
    package_data={"sewer": ["*.json"]},
    zip_safe=False,
    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    # entry_points={
    #     'console_scripts': [
    #         'sample=sample:main',
    #     ],
    # },
    entry_points={"console_scripts": ["sewer=sewer.cli:main", "sewer-cli=sewer.cli:main"]},
    ### CANNOT FIX ### black sometimes ignores explicit version and adds the invalid comma anyway
    # fmt: off
    **meta
    # fmt: on
)
