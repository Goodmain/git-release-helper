from setuptools import setup, find_packages

setup(
    name="git-release-helper",
    version="0.1.0",
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
            "release=git_release_helper.cli:main",
        ],
    },
    author="User",
    author_email="user@example.com",
    description="A helper tool for creating GitHub releases",
    keywords="git, github, release",
    python_requires=">=3.6",
)
