from setuptools import setup, find_packages

setup(
    name="nhnscan",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'nhnscan=nhnscan.cli:main',
        ],
    },
    install_requires=[],
    python_requires='>=3.7',
    author="David",
    description="Security Scanner - Simple wrapper for nmap and snmpwalk",
    keywords="security scanner nmap snmp",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
    ],
)
