from setuptools import setup, find_packages

with open("README.md", encoding="utf8") as readme_file:
    readme_txt = readme_file.read()

setup(
    name='starpso',
    version='0.1.0',
    author='Michalis Vrettas, PhD',
    author_email='michail.vrettas@gmail.com',
    description='Particle Swarm Optimization algorithms toolbox in Python3',
    long_description=readme_txt,
    long_description_content_type='text/markdown',
    url='https://github.com/vrettasm/PyStarPSO',
    packages=find_packages(exclude=["docs", "unittests"]),
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
    install_requires=[
        'numpy',
        'scipy',
        'numba',
        'joblib',
    ],
)
