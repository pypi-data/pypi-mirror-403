# Minimal makefile for Sphinx documentation

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS     ?= -W --keep-going -n --color -v
SPHINXBUILD    ?= sphinx-build
SOURCEDIR       = source
BUILDDIR        = build
APIDOCTEMPLATES = $(SOURCEDIR)/_templates
APISOURCE       = ../src/calibpipe
DIAGRAMSDIR     = $(SOURCEDIR)/introduction/diagrams

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile clean #apidoc diagrams

diagrams:
	@for file in $(wildcard $(DIAGRAMSDIR)/*.mmd); do \
		mmdc -p $(DIAGRAMSDIR)/puppeteer-config.json -i $$file -o $${file%.mmd}.svg; \
	done

apidoc:
	sphinx-apidoc -M -t $(APIDOCTEMPLATES) -o $(SOURCEDIR)/calibpipe_api $(APISOURCE)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile apidoc diagrams
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

clean:
	rm -rf $(SOURCEDIR)/calibpipe_api
	rm -rf $(DIAGRAMSDIR)/*.svg
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
