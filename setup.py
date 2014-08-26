from setuptools import setup, find_packages

setup(
    name = "pyadds",
    version = "0.1",
    packages = find_packages(),
    scripts = [],
    install_requires = [
            'docutils>=0.3',
            ],
    package_data = {
        '': ['*.txt', '*.rst'],
    },

    # metadata for upload to PyPI
    author = "wabu",
    author_email = "wabu@fooserv.net",
    description = "miscellaneous helpfull stuff for python",
    license = "MIT",
    keywords = "python tools utils",
    url = "https://github.com/wabu/pyadds",
)
