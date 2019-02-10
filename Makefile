# #!/usr/bin/env make -f
# See LICENSE file for copyright and license details.

VERSION = $(shell git tag -l|tail -n 1|sed -e 's/^v//')
DESTDIR = /usr
SCRIPTS = scripts/nvim.vmux scripts/nvim-qt.vmux scripts/vim.vmux scripts/gvim.vmux scripts/kak.vmux
SRC = vmux/__main__.py

all: install-wrapper

clean:
	@echo cleaning
	@rm -f vmux-${VERSION}.tar.gz

dist: clean
	@echo creating dist tarball
	mkdir -p vmux-${VERSION}
	cp -R LICENSE Makefile README.md ${SRC} ${SCRIPTS} vmux-${VERSION}
	tar -zcf vmux-${VERSION}.tar.gz vmux-${VERSION}
	rm -rf vmux-${VERSION}

install: vmux
	@echo installing executable file to ${DESTDIR}${PREFIX}/bin
	mkdir -p ${DESTDIR}${PREFIX}/bin
	cp -f ${SRC} ${DESTDIR}${PREFIX}/bin/vmux
	chmod 755 ${DESTDIR}${PREFIX}/bin/vmux

install-scripts: install $(SCRIPTS)
	@echo installing wrapper scripts to ${DESTDIR}${PREFIX}/bin
	mkdir -p ${DESTDIR}${PREFIX}/bin
	cp -f ${SCRIPTS} ${DESTDIR}${PREFIX}/bin
	chmod 755 $(foreach script,$(SCRIPTS),${DESTDIR}${PREFIX}/bin/$(shell basename $(script)))

uninstall:
	@echo removing executable files from ${DESTDIR}${PREFIX}/bin
	rm -f ${DESTDIR}${PREFIX}/bin/vmux
	rm -f $(foreach script,$(SCRIPTS),${DESTDIR}${PREFIX}/bin/$(shell basename $(script)))

.PHONY: clean dist install install-scripts uninstall
