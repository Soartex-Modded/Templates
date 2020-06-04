from setuptools import setup

setup(
    package_data={
        "resource_manager.utilities": [
            "root/pack.png",
            "root/README.md"
        ],
        "resource_manager": [
            "configs/pipelines.toml",
            "configs/resources.toml"
        ]
    },
    entry_points={
        'console_scripts': [
            'soartex = resource_manager.main:main',
        ],
    },
)
