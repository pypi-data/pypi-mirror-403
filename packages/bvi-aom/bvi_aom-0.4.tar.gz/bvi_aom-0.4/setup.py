from setuptools import setup, find_packages

with open("README.md", "r") as f:
    description = f.read()

setup(
    name='bvi_aom',
    version='0.4',
    packages=find_packages(),
    install_requires = [
        'wget'
    ],
    entry_points={
        "console_scripts": [
            "bvi-aom = bvi_aom:main"
        ]
    },
    long_description=description,
    long_description_content_type="text/markdown"
)