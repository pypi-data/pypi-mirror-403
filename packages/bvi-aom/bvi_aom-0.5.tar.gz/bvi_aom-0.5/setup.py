from setuptools import setup, find_packages

with open("README.md", "r") as f:
    description = f.read()

with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name='bvi_aom',
    version='0.5',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "bvi-aom = bvi_aom:main"
        ]
    },
    long_description=description,
    long_description_content_type="text/markdown"
)