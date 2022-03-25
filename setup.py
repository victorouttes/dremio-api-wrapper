from setuptools import setup
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='dremio_api_wrapper',
    packages=[
        'dremio',
    ],
    version='1.0.0',
    license='MIT',
    description='Wrapper to use Dremio rest api.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Victor Outtes',
    author_email='victor.outtes@gmail.com',
    url='https://github.com/victorouttes/dremio-api-wrapper',
    keywords=['dremio'],
    install_requires=[
        'certifi==2021.5.30',
        'charset-normalizer==2.0.6',
        'idna==3.2',
        'requests==2.26.0',
        'urllib3==1.26.6',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)