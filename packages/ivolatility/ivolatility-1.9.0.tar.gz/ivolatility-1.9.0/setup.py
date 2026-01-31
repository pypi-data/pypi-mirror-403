from setuptools import setup, find_packages

setup(
    name='ivolatility',
    version='1.9.0',
    description='IVolatility API wrapper package',
    url='https://redocly.github.io/redoc/?nocors&url=https://restapi.ivolatility.com/api-docs',
    author='IVolatility',
    author_email='support@ivolatility.com',
    license='BSD 2-clause',
    packages=['ivolatility'],
    install_requires=['pandas',
                      'requests'
                      ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: BSD License',  
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
