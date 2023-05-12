from setuptools import setup

setup(
    name='medsenger_api',
    version='0.1.29',
    description='Python SDK for Medsenger.AI',
    url='https://github.com/roctbb/medsenger_api',
    author='Rostislav Borodin',
    author_email='borodin@medsenger.ru',
    license='BSD 2-clause',
    packages=['medsenger_api'],
    install_requires=['requests', 'python-magic'],
    package_data={'': ['*']},
    include_package_data=True,
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.7',
    ],
)