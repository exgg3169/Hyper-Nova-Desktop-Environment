PREFIX  ?= /usr
DESTDIR ?=
PYTHON  ?= python3
LIBDIR  := $(PREFIX)/lib/hypernova
DATADIR := $(PREFIX)/share/hypernova
SIZES   := 16 24 32 48 64 128 256

.PHONY: all install uninstall check run run-settings

all:

install:
	install -d $(DESTDIR)$(LIBDIR)/hypernova
	install -m644 hypernova/*.py $(DESTDIR)$(LIBDIR)/hypernova/
	install -d $(DESTDIR)$(PREFIX)/bin
	for bin in hypernova-shell hypernova-settings hypernova-session; do \
		sed -e 's|@LIBDIR@|$(LIBDIR)|g' -e 's|@DATADIR@|$(DATADIR)|g' bin/$$bin > $(DESTDIR)$(PREFIX)/bin/$$bin; \
		chmod 755 $(DESTDIR)$(PREFIX)/bin/$$bin; \
	done
	install -d $(DESTDIR)$(DATADIR)/styles
	install -m644 data/styles/*.css $(DESTDIR)$(DATADIR)/styles/
	for theme in data/themes/*; do \
		install -d $(DESTDIR)$(PREFIX)/share/themes/$$(basename $$theme)/openbox-3; \
		install -m644 $$theme/openbox-3/* $(DESTDIR)$(PREFIX)/share/themes/$$(basename $$theme)/openbox-3/; \
	done
	install -Dm644 data/xsessions/hypernova.desktop $(DESTDIR)$(PREFIX)/share/xsessions/hypernova.desktop
	install -Dm644 data/applications/hypernova-settings.desktop \
		$(DESTDIR)$(PREFIX)/share/applications/hypernova-settings.desktop
	for size in $(SIZES); do \
		install -Dm644 data/icons/hicolor/$${size}x$${size}/apps/hypernova.png \
			$(DESTDIR)$(PREFIX)/share/icons/hicolor/$${size}x$${size}/apps/hypernova.png; \
	done
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/hypernova-desktop/LICENSE

uninstall:
	rm -rf $(DESTDIR)$(LIBDIR) $(DESTDIR)$(DATADIR)
	rm -f $(DESTDIR)$(PREFIX)/bin/hypernova-shell $(DESTDIR)$(PREFIX)/bin/hypernova-settings \
		$(DESTDIR)$(PREFIX)/bin/hypernova-session
	rm -rf $(DESTDIR)$(PREFIX)/share/themes/HyperNova-XP $(DESTDIR)$(PREFIX)/share/themes/HyperNova-7 \
		$(DESTDIR)$(PREFIX)/share/themes/HyperNova-10 $(DESTDIR)$(PREFIX)/share/themes/HyperNova-Mac
	rm -f $(DESTDIR)$(PREFIX)/share/xsessions/hypernova.desktop \
		$(DESTDIR)$(PREFIX)/share/applications/hypernova-settings.desktop
	for size in $(SIZES); do rm -f $(DESTDIR)$(PREFIX)/share/icons/hicolor/$${size}x$${size}/apps/hypernova.png; done

# Byte-compiles every module and runs the headless smoke test (needs Xvfb + Openbox).
check:
	$(PYTHON) -m compileall -q hypernova
	PYTHON=$(PYTHON) sh tests/smoke.sh

# Runs the shell from the source tree inside the current X session (for development).
run:
	PYTHONPATH=. $(PYTHON) -m hypernova

run-settings:
	PYTHONPATH=. $(PYTHON) -m hypernova settings
