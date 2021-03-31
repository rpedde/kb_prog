from setuptools import setup, find_packages

setup(
    name='kbprog',
    version='1.0.0',
    url='https://github.com/rpedde/kb_prog',
    author='Ron Pedde',
    author_email='ron@pedde.com',
    description='keyboard editor for some subset of via boards',
    packages=find_packages(),
    install_requires=[
        'evdev',
        'pygame',
        'pyusb',
        'hid'
    ])
