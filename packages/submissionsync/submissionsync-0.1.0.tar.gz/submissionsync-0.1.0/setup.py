from setuptools import setup, find_packages

setup(
    name='submissionsync',
    version='0.1.0',
    description='Create shortcuts to latest submitted assignment versions',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/UTCSheffield/ms-teams-latest-submitted-version',
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=[
        'seedir>=0.4.0',
        'pywin32>=305; sys_platform == "win32"',
    ],
    entry_points={
        'console_scripts': [
            'submissionsync=submissionsync.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: Microsoft :: Windows',
    ],
)
