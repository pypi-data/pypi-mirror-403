[![Coverage Status](https://codeberg.org/pteysseyre/vlf4ions_library/src/branch/main/reports/coverage/coverage-badge.svg?dummy=8484744)](https://codeberg.org/pteysseyre/vlf4ions_library/src/branch/main/reports/coverage/coverage-badge.svg) [![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


This is the most up-to-date version of the *vlf4ions* Python library, which is hosted on [Codeberg](https://codeberg.org/pteysseyre/vlf4ions_library). This library is designed for VLF-antenna owners. It allows the detection of solar flares in real-time from ground-based VLF data. An estimate of the solar X-ray flux from the Sun is also made possible.

Though it was designed with an AWESOME instrument in mind, it can be adapted to any type of VLF antennas, provided that both amplitude and phase measurements are available for any transmitter of interest.

# Installation

To install the package, you can simply type in a virtual environment:

````
pip install vlf4ions
````

This should download the more recent version.


To install the package, go to [Release](https://codeberg.org/pteysseyre/vlf4ions_library/releases) at the top of the page and download the latest version. In the `zip` or `tar.gz` folder, you should find a file ending in `.whl`. In a terminal, write

````
pip install file_in_.whl
````

Note that sometimes we also implement new features or fix some bugs, but this version is not yet released (usually before it doesn't differ enough from the previous one.) In this case, you can download these stable sub-version from the [Tags](https://codeberg.org/pteysseyre/vlf4ions_library/tags) page. The differences between each versions are outlined in the CHANGELOG file

# Testing

To test the entire package, you can run (when you are in the top folder)

````
pytest
````

This is the minimal version to check that all tests are passed. If, however, you're developping your own branch of the repository, or if you want the coverage report, run:

````
pytest --cov=vlf4ions --cov-report=xml:reports/coverage/coverage.xml
coverage html
genbadge coverage -o reports/coverage/coverage-badge.svg
````

This will create a full coverage report and a badge to display the new coverage

# Documentation

The documentation may be found [here](https://vlf4ions.readthedocs.io/en/latest/).

# Contributing

Any feedback or contribution is very welcome. Please use pull requests to contribute to this package, or directly open an issue if you notice that something is wrong or can be enhanced.

Any question may also be sent to me by email if needed, or by pinging me on Codeberg.

# Acknowledgements

Many thanks to Pierre-Yves Martin and Xavier Bonnin for their help with the licence and all other aspects of publishing an open-source project. This project really would have taken much longer to deploy if not for their advice !

# Citing

If you use this library in a scientific context, please cite the paper 'Real-time detection of solar flares from ground-based data' by P. Teysseyre, C. Briand and M. Cohen. As of now (January 2025), it is still in review.
