from pathlib import Path
from setuptools import setup, find_packages
import subprocess

BASE_DIR = Path(__file__).resolve().parent
VERSION_FILE = BASE_DIR / "VERSION"

def read_requirements():
    req_file = BASE_DIR / "requirements.txt"
    return req_file.read_text().splitlines() if req_file.exists() else []


def read_readme():
    readme_file = BASE_DIR / "README.md"
    return readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

def get_version():
    """Get the version from Git tags or the VERSION file."""
    try:
        # Get the latest Git tag
        version = subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"], stderr=subprocess.DEVNULL).decode().strip()
        return version
    except subprocess.CalledProcessError:
        return "1.0.0"  # Default version if all else fails
    
setup(
    name="liberty-airflow-plugins",                
    version=get_version(),                
    description="Plugins for Liberty Airflow", 
    long_description=read_readme(),  
    long_description_content_type="text/markdown",
    author="Franck Blettner",                
    author_email="franck.blettner@nomana-it.fr ",
    url="https://nomana-it.fr",  
    packages=find_packages(),         
    include_package_data=True, 
    install_requires=read_requirements(),
    classifiers=[                       
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.12',            
)