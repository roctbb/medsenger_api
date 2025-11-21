from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='medsenger_api',
    version='0.1.94',
    description='Python SDK for Medsenger.AI',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/roctbb/medsenger_api',
    author='Rostislav Borodin',
    author_email='borodin@medsenger.ru',
    license='BSD 2-clause',
    packages=['medsenger_api'],
    install_requires=['requests', 'python-magic', 'grpcio', 'grpcio-tools', 'sentry-sdk'],
    package_data={'protocol': ['*']},
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.7',
    ],
    include_package_data=True
)