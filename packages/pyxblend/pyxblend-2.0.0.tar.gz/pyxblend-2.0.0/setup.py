from setuptools import setup, find_packages
import os

# Read the contents of your README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pyxblend',
    version='2.0.0',
    description='Professional-grade Python obfuscation and Cython-based compilation suite.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='PythonToday',
    author_email='contact@pythontoday.com',
    url='https://github.com/pythontoday/pyxblend',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Security',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Compilers',
    ],
    keywords='obfuscation, encryption, cython, security, protection, compilation',
    install_requires=[
        'python_minifier>=2.9.0',
        'cython>=3.0.0',
    ],
    python_requires='>=3.8',
    project_urls={
        'Bug Reports': 'https://github.com/pythontoday/pyxblend/issues',
        'Source': 'https://github.com/pythontoday/pyxblend',
        'Documentation': 'https://github.com/pythontoday/pyxblend/wiki',
    },
    include_package_data=True,
    zip_safe=False,
)
