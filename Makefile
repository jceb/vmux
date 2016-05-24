# #!/usr/bin/env make -f
# See LICENSE file for copyright and license details.

VERSION = 0.1
SRC = vmux

clean:
	@echo cleaning
	@rm -f vmux-${VERSION}.tar.gz

dist: clean
	@echo creating dist tarball
	@mkdir -p vmux-${VERSION}
	@cp -R LICENSE Makefile README.md ${SRC} vmux-${VERSION}
	@tar -zcf vmux-${VERSION}.tar.gz vmux-${VERSION}
	@rm -rf vmux-${VERSION}

install: $(SRC)
	@echo installing executable file to ${DESTDIR}${PREFIX}/bin
	@mkdir -p ${DESTDIR}${PREFIX}/bin
	@cp -f vmux ${DESTDIR}${PREFIX}/bin
	@chmod 755 ${DESTDIR}${PREFIX}/bin/vmux

uninstall:
	@echo removing executable file from ${DESTDIR}${PREFIX}/bin
	@rm -f ${DESTDIR}${PREFIX}/bin/vmux

.PHONY: clean dist install uninstall
