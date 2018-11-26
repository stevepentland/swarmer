import setuptools

requires = [
    'redis==2.10.6',
    'falcon==1.4.1',
    'falcon-json==0.0.1',
    'docker==3.5.1',
    'docker-pycreds==0.3.0',
    'ulid-py==0.0.7',
    'requests==2.20.0',
    'gunicorn==19.9.0'
]

setuptools.setup(
    name='swarmer',
    version='0.4.2',
    author='Steve Pentland',
    author_email='swarmerproject@outlook.com',
    license='MIT',
    description='Docker Swarm One-Shot Service Runner',
    long_description=open('README.md', 'r').read(),
    long_description_content_type='text/markdown',
    install_requires=requires,
    python_requires='>=3.6, <4',
    url='https://github.com/stevepentland/swarmer',
    packages=setuptools.find_packages(exclude=['tests*']),
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Topic :: System :: Distributed Computing',
        'Topic :: Utilities'
    ],
    entry_points={
        'console_scripts': [
            'swarmer = swarmer.swarmer:main'
        ],
        'swarmer.credentials': [
            'aws = auth.aws.awsecr:AwsAuthenticator [AWS]',
            'basic = auth.basic.basicauth:BasicAuthenticator'
        ]
    },
    keywords='docker swarm',
    extras_require={
        'AWS': ['boto3>=1.9,<1.10']
    }
)
