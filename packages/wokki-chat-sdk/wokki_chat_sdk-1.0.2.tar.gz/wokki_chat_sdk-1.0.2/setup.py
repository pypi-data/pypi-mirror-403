from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='wokki-chat-sdk',
    version='1.0.2',
    description='Python SDK to make bots for Wokki Chat',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Bjarnos & wokki20',
    url='https://github.com/levkris/Wokki-Chat-Python-SDK',
    license='Apache-2.0',
    packages=find_packages(include=['wokkichat', 'wokkichat.*']),
    install_requires=[
        'python-socketio[client]',
        'aiohttp'
    ],
    python_requires='>=3.6',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Topic :: Communications :: Chat',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Intended Audience :: Developers',
        'Environment :: Web Environment',
        'Framework :: AsyncIO',
        'Operating System :: OS Independent',
        'Typing :: Typed',
        'License :: OSI Approved :: Apache Software License',
    ],
)