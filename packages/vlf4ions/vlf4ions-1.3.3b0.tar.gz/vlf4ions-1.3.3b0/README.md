
[![Python package](https://github.com/pteysseyre/vlf4ions_library/actions/workflows/main.yml/badge.svg)](https://github.com/pteysseyre/vlf4ions_library/actions/workflows/main.yml)
[![codecov](https://codecov.io/github/pteysseyre/vlf4ions_library/graph/badge.svg?token=588B97ITBC)](https://codecov.io/github/pteysseyre/vlf4ions_library)


This is the cleaner version of the vlf4ions library, which I am using both to store the code and the different versions, but also to learn how to do it properly.


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

# How to launch the script at the antenna if it has stopped ?

For the antennas in Nançay and La Réunion, this is done in the same way:

1. Open an `Anaconda Powershell` terminal
2. Move to the `Desktop/VLF` folder
3. Move to the correct Python environment: in the terminal, type
```ruby
conda deactivate
conda activate spyder # Note: at la Réunion, type envrealtime instead of spyder
```

4. Launch the script
```ruby
python Detection_script.py # Detection_script_LR.py at La Réunion
```

If everything is fine, you should see an output like
```ruby
Done - NRK - 13:00:00
```
after a few seconds. 



