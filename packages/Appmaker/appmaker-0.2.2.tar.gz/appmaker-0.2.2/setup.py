from setuptools import setup

setup(
    name='Appmaker',
    version='0.2.2',
    packages=['appmaker'],
    url='https://github.com/Pixel-Master/appmaker',
    license='GNU GPL v3.0',
    author='Pixel Master',
    author_email='',
    description='Command line tool to package executable into an .app bundle',
    long_description=''.join(open('README.rst', encoding='utf-8').readlines()),
    keywords=['cmd', 'executable', 'macOS'],
    include_package_data=True,
    install_requires=[''],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: MacOS",
    ],
    entry_points={'console_scripts': ['appmaker=appmaker.appmaker:main', 'mkapp=appmaker.appmaker:main'], }

)
