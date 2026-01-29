from setuptools import setup, find_packages

setup(
    name="opsec-panel",
    version="1.0.0",
    packages=find_packages(),
    author="Khobz UHQ",
    description="OPSEC panel installer",
    python_requiers=">=3.8",
    entry_points={
        'console_scripts': [
            "opsec-install=opsec.install:install_panel"
        ]
    },
    
)