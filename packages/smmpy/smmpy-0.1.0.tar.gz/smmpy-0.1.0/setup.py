from setuptools import setup

setup(
    name='smmpy',
    version='0.1.0',
    description='A Python client for SMM panels',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='sleepyvani',
    author_email='vanixjnk@gmail.com',
    url='https://github.com/sleepyvani/smmpy',
    py_modules=['smmpy'],
    install_requires=[
        'requests',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
