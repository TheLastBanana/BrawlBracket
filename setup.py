from setuptools import setup

setup(
    name='BrawlBracket',
    version='0.1',
    description='A web app to simplify running Brawlhalla tournaments.',
    author='Elliot Colp and Braedy Kuzma',
    install_requires=[
        'python-dateutil==2.2',
        'bidict==0.9.0.post1',
        'Flask==0.10.1',
        'Flask-Login==0.3.2',
        'Flask-SocketIO==1.2',
        'eventlet==0.17.4',
        'pytest==2.8.7'
    ]
)
