from setuptools import setup, find_packages

setup(
    name='netHighTech_STT', # Naya package naam
    version='1.0.8', # Naya version number
    author='Zubair Khan',
    author_email='zubairdev00@gmail.com',
    description='Speech recognition Jarvis package',
    packages=find_packages(),
    include_package_data=True, # Assets shamil karne ke liye
    install_requires=[
        'selenium',
        'webdriver-manager',
    ],
)