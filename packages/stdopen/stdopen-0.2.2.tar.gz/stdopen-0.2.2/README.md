# Getting started with stdopen

__version__: `0.2.2`

This is a wrapper around Python's `open` (or other open methods), that will automate file-like object creation either by opening a file or from STDIN/STDOUT. It also provides the option writing to a temp file which is seamlessly copied over to the desired output directory upon successful closing, or deleted upon error. It will also pass through (back) any iterators.

All of the functionality described above is particulay useful when implementing cmd-line programs.

There is [online](https://cfinan.gitlab.io/stdopen) documentation for stdopen.

## Installation instructions

### pip install

```
pip install stdopen
```


### Installation using conda
A conda build is also available for Python v3.9 - v3.13 on linux-64/osX-64. Although please note that all development and testing is performed in linux-64.
```
conda install -c conda-forge -c cfin stdopen
```

## Next steps...
If you want to run the tests after install you will need to have cloned the repo and run ``pytest <REPO-ROOT>/tests``.

## Change log
You can view the changelog [here](CHANGELOG.md).

