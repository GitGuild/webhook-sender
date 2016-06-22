from setuptools import setup

classifiers = [
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 2",
    "Topic :: Software Development :: Libraries",
]

setup(
    name='webhook-sender',
    version='0.1.0',
    packages=['webhook_sender'],
    url='https://github.com/gitguild/webhook_sender',
    license='MIT',
    classifiers=classifiers,
    author='Ira Miller',
    author_email='ira@gitguild.com',
    description='A helper for sending webhooks, with automatic retry and CLI.',
    setup_requires=['pytest-runner'],
    install_requires=[
        'sqlalchemy>=1.0.9',
        'requests'
    ],
    tests_require=['pytest', 'flask>=0.10.0', 'pytest-flask', 'pytest-cov']
)
