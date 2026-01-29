from setuptools import setup, find_packages

setup(
    name='wedopython_rpi4',
    version='1.2.0',
    packages=find_packages(),
    install_requires=['gattlib==0.20210616'],
    zip_safe=False,
    include_package_data=True,
    author="Evangelia Anastasaki",
    author_email="eveanast@gmail.com",
    description="Python BLE library for LEGO WeDo 2.0 using gattlib (Raspberry Pi 4)",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/eveanast/wedopython_rpi4",
    project_urls={
        "Documentation": "https://github.com/eveanast/wedopython_rpi4#readme",
        "Source": "https://github.com/eveanast/wedopython_rpi4",
        "Tracker": "https://github.com/eveanast/wedopython_rpi4/issues",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Education",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
    ],
    python_requires='>=3.7',
)