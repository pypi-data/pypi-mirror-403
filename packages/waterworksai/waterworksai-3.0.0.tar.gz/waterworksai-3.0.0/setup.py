from setuptools import setup, find_packages

setup(
    name='waterworksai',
    version='3.0.0',
    author='D. Rehn',
    description='Official Python client for waterworks.ai API',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=[
        'pandas>=1.5',
        'requests>=2.28',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Hydrology'
    ],
    python_requires='>=3.9',
)
