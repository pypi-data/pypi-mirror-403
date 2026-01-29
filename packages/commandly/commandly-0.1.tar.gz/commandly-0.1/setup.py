from setuptools import setup

setup(
    name='commandly',
    version='0.1',
    author='Pulkit Bansal',
    author_email='bansalpulkit3122@google.com',
    description='A command line utility package',
    long_description_content_type='text/markdown',
    packages=['commandly'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    install_requires=[
    ],
    entry_points={
        "console_scripts":[
            "commandly-hello=commandly:hello",
        ]
    }
)