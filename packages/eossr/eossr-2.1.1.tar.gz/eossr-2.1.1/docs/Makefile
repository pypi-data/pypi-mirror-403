# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?= -j4
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Makefile

# Target to source .env file
source-token:
	@if [ -f "../zenodo.token" ]; then \
		set -a; \
		source ../zenodo.token; \
		set +a; \
		echo "../zenodo.token file sourced successfully."; \
	else \
		echo "../zenodo.token file does not exist."; \
	fi


# New target for 'doc' that depends on 'source-token'
doc: source-token
	@$(SPHINXBUILD) -M doc "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
