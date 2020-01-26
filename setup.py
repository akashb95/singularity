from setuptools import setup

setup(
    name='stardust',
    version='0.0.1',
    packages=['lightingComponents'],
    url='https://github.com/akashb95/singularity',
    license='',
    author='Akash B',
    author_email='akash.bhattacharya.18@ucl.ac.uk',
    description='Fun & Games with gRPC.',
    install_requires=[
        "grpcio",
        "grpcio-tools", 'python-dotenv'
    ]
)
