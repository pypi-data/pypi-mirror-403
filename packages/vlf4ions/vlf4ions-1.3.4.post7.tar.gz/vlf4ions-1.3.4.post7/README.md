[![Coverage Status](./reports/coverage/coverage-badge.svg)](./htmlcov/index.html) [![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)


This is the cleaner version of the vlf4ions library, which I am using both to store the code and the different versions, but also to learn how to do it properly.
NOTE: This is a version of the code migrated from GitHub. It is the most up-to-date one, but some links to issues for previous commits may not work anymore

This library is designed for VLF-antenna owners. It allows the detection of solar flares in real-time from ground-based VLF data. An estimate of the solar X-ray flux from the Sun is also made possible.
Though it was designed with an AWESOME instrument in mind, it can be adapted to any type of VLF antennas, provided that both amplitude and phase measurements are available for any transmitter of interest.

# Testing

To test the entire package, you can run

````
pytest
````

This is the minimal version to check that all tests are passed. If, however, you're developping your own branch of the repository, or if you want the coverage report, run:

````
pytest --cov=vlf4ions --cov-report=xml:reports/coverage/coverage.xml # Tests + xml report
coverage html # Generate html report (to know where to work next)
genbadge coverage -o reports/coverage/coverage-badge.svg # Generates badge
````

This will create a full coverage report and a badge to display the new coverage

# Documentation

The documentation may be found at 'https://vlf4ions.readthedocs.io/en/latest/'.

# Contributing

Any feedback or contribution is very welcome. Please use pull requests to contribute to this package, or directly open an issue if you notice that something is wrong or can be enhanced.

Any question may also be sent to me by email if needed, or by pinging me on Codeberg.

# Aknowledgements

Many thanks to Pierre-Yves Martin and Xavier Bonnin for their help with the licence and all other aspects of publishing an open-source project. This project really would have taken much longer to deploy if not for their advice !