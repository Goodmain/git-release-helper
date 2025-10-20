from setuptools import setup, find_packages

setup(
    name="git-release-helper",
    version="0.2.0",
    packages=find_packages(),
    package_data={
        "": ["config.yml.template"],
    },
    install_requires=[
        "click",
        "gitpython",
        "PyYAML",
        "requests",
    ],
    entry_points={
        "console_scripts": [
            "rh=git_release_helper.cli:main",
        ],
    },
    author="Goodmain",
    author_email="iskrinvv@gmail.com",
    description="A helper tool for creating GitHub releases",
    keywords="git, github, release",
    python_requires=">=3.6",
)
