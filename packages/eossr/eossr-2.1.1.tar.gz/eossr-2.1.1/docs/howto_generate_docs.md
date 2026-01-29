# How to generate eossr documentation - for developers


1. Install doc requirements:
```
pip install -r requirements.txt
```

1. (re)-Generate docstring_sources:
```
sphinx-apidoc -o docstring_sources ../eossr
```

1. Tweak generated docstring:
- remove unwanted rst files
- remove unwanted (empty) modules content sections in rst files
- remove section title in `eossr.rst` that just makes an extra menu entry
- remove section `Submodules` in some rst files

1. Add CLI documentation if necessary:
- add a new file in `docstring_sources/eossr_cli` with the name of the CLI command

1. Generate docs:
```
make html
```

Note: to avoid builing jupyter notebook (time consuming), use:
```
make html SPHINXOPTS="-D nbsphinx_execute='never'"
```
