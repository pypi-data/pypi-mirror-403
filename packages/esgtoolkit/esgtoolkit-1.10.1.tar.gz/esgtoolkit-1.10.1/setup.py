import subprocess
from installr import check_r_installed, install_r
from os import path
from setuptools import setup, find_packages

# Check if R is installed; if not, install it
if not check_r_installed():
    print("Installing R...")
    install_r()
else:
    print("No R installation needed.")

subprocess.run(['pip', 'install', 'rpy2>=3.4.5'])

"""The setup script."""
here = path.abspath(path.dirname(__file__))

# get the dependencies and installs
with open(
    path.join(here, "requirements.txt"), encoding="utf-8"
) as f:
    all_reqs = f.read().split("\n")

install_requires = [
    x.strip() for x in all_reqs if "git+" not in x
]
dependency_links = [
    x.strip().replace("git+", "")
    for x in all_reqs
    if x.startswith("git+")
]

setup(
    author="T. Moudiki",
    author_email='thierry.moudiki@gmail.com',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Diffusion models for finance, insurance, economics, physics",
    install_requires=install_requires,
    license="BSD Clause Clear license",
    long_description="Python port of R package 'esgtoolkit' (https://techtonique.github.io/esgtoolkit/)",
    include_package_data=True,
    keywords='esgtoolkit',
    name='esgtoolkit',
    packages=find_packages(include=['esgtoolkit', 'esgtoolkit.*']),
    test_suite='tests',    
    url='https://github.com/Techtonique/esgtoolkit_python',
    version='1.10.1',
    zip_safe=False,
)
