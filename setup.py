from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='ai_code_reviewer',
    version='0.0.1',
    author='Dmitrii Rashchenko',
    author_email='dimitree54@gmail.com',
    packages=find_packages(),
    description='Useful classes extending langchain library',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/dimitree54/ai_code_reviewer',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: CC BY-NC-SA License',
        'Operating System :: OS Independent',
    ],
    install_requires=required
)
