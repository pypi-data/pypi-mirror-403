from setuptools import setup, find_packages

# with open("README.md", "r", encoding="utf-8") as f:
#     long_description = f.read()

setup(
    name='euroncal_test', # Required - must be unique on PyPI
    version='0.1.0', # Required
    author='Vivek', # Required
    author_email='srvivek86@gmail.com', # Required
    description='A simple calculator package', # Required
    long_description="Long description of the package", # Optional
    long_description_content_type='text/markdown',
    url='https://github.com', # Optional - Project home page
    packages=find_packages(), # Required - automatically finds all packages
    entry_points={
    "console_scripts": [
        "euroncal=calculator:main"
    ]
}, # Optional - for command-line scripts
    # install_requires=[
    #     'numpy', # Example dependency
    #     'requests>=2.25.0', # Example dependency with version specifier
    # ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9', # Required
)
