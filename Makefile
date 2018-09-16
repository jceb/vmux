# #!/usr/bin/env make -f
# See LICENSE file for copyright and license details.

VERSION = $(shell git tag -l|tail -n 1|sed -e 's/^v//')
DESTDIR = /usr
SCRIPTS = scripts/nvim.vmux scripts/vim.vmux scripts/gvim.vmux scripts/kak.vmux
SRC = vmux

all: install-wrapper

clean:
	@echo cleaning
	@rm -f vmux-${VERSION}.tar.gz

dist: clean
	@echo creating dist tarball
	mkdir -p vmux-${VERSION}
	cp -R -t vmux-${VERSION} LICENSE Makefile README.md ${SRC} scripts
	tar -zcf vmux-${VERSION}.tar.gz vmux-${VERSION}
	rm -rf vmux-${VERSION}

install: vmux
	@echo installing executable file to ${DESTDIR}${PREFIX}/bin
	mkdir -p ${DESTDIR}${PREFIX}/bin
	cp -f -t ${DESTDIR}${PREFIX}/bin vmux
	chmod 755 ${DESTDIR}${PREFIX}/bin/vmux

install-wrapper: install $(SCRIPTS)
	@echo installing wrapper scripts to ${DESTDIR}${PREFIX}/bin
	mkdir -p ${DESTDIR}${PREFIX}/bin
	cp -f -t ${DESTDIR}${PREFIX}/bin ${SCRIPTS}
	$(foreach script,$(SCRIPTS),$(shell chmod 755 ${DESTDIR}${PREFIX}/bin/$(shell basename $(script))))

uninstall:
	@echo removing executable files from ${DESTDIR}${PREFIX}/bin
	rm -f ${DESTDIR}${PREFIX}/bin/vmux
	$(foreach script,$(SCRIPTS),$(shell rm -f ${DESTDIR}${PREFIX}/bin/$(shell basename $(script))))

.PHONY: clean dist install install-wrapper uninstall
