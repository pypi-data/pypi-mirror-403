![Coverage Status](./reports/coverage/coverage-badge.svg)

This is the cleaner version of the vlf4ions library, which I am using both to store the code and the different versions, but also to learn how to do it properly.
NOTE: This is a version of the code migrated from GitHub. It is the most up-to-date one, but some links to issues for previous commits may not work anymore

This library is designed for VLF-antenna owners. It allows the detection of solar flares in real-time from ground-based VLF data. An estimate of the solar X-ray flux from the Sun is also made possible.
Though it was designed with an AWESOME instrument in mind, it can be adapted to any type of VLF antennas, provided that both amplitude and phase measurements are available for any transmitter of interest.

This is a test

# How to read the documentation ?

So far, the documentation is not published, as the project is not public (and I didn't find a way to publish it privately without paying).
All the files are in 'docs'. To read them, please follow the steps below:

## 1st option: read the `html` files directly from the `docs/build/html` folder

To do so, you only have to download them, and click on the `index.html` file

## 2nd option: re-make the `html` file from the `.rst` files
Run in a terminal if this is the first time reading them:

```ruby
pip install sphinx # to create the docs
pip install sphinx_rtd_theme # To install the theme for the documentation
```

Then, in the `docs` folder, please run in a terminal
```ruby
make html
```
A `doctree` and a `html` folders will then be created. To open the documentation, please click on the `index.html` file in the `html` folder.

## 3rd option: read them online

A simpler version is just to click on the docs in GitLab, but a lot of the referencing between files will be lost, as well as the structure of the documentation.

# Contributing

Any feedback or contribution is very welcome. Please use pull requests to contribute to this package, or directly open an issue if you notice that something is wrong or can be enhanced.

Any question may also be sent to me by email if needed, or by pinging me on Codeberg.

# Aknowledgements

Many thanks to Pierre-Yves Martin and Xavier Bonnin for their help with the licence and all other aspects of publishing an open-source project. This project really would have taken much longer to deploy if not for their advice !