# Getting Started with stdopen

__version__: `0.1.0a1`

This is a wrapper around Python's `open` (or other open methods), that will automate file-like object creation either from opening a file or from STDIN/STDOUT. It also provides the option writing to a temp file which is seamlessly copied over to the desired output directory upon successful closing, or deleted upon error.

All of the functionality described above is particulay useful when implementing cmd-line programs.

There is [online](https://cfinan.gitlab.io/stdopen) documentation for stdopen and offline PDF documentation can be downloaded [here](https://gitlab.com/cfinan/stdopen/-/blob/main/resources/pdf/stdopen.pdf).

## Installation instructions
At present, no packages exist yet on PyPy. Therefore it is recommended that it is installed in either of the two ways listed below. First, clone this repository and then `cd` to the root of the repository.

```
# Change in your package - this is not in git
git clone git@gitlab.com:cfinan/stdopen.git
cd stdopen
```

### Installation not using any conda dependencies
If you are not using conda in any way then install the dependencies via `pip` and install stdopen as an editable install also via pip:

Install dependencies:
```
python -m pip install --upgrade -r requirements.txt
```

For an editable (developer) install run the command below from the root of the stdopen repository (or drop `-e` for static install):
```
python -m pip install -e .
```

### Installation using conda
A conda build is also available for Python v3.8 on linux-64/osX-64.
```
conda install -c cfin stdopen
```

If you are using conda and require anything different then please install with pip and install the dependencies with the environments specified in `resources/conda_env`. There is also a build recipe in `./resourses/build/conda` that can be used to create new packages.

## Next steps...
If cloned and installed via pip you can also run the tests using ``pytest ./tests``
