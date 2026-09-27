## Cherokee: Makefile.am  -*- makefile -*-

cherokeewwwdir = "@WWW_ROOT@"
cherokeewwwcssdir = "@WWW_ROOT@/css"
cherokeewwwjsdir = "@WWW_ROOT@/js"

cherokeewwwimagesdir = "@WWW_ROOT@/images"
cherokeewwwimages_DATA = \
favicon.ico \
default-bg.png \
cherokee-logo.png \
powered_by_cherokee.png

cherokeewwwcss_DATA = css/cherokee.css
cherokeewwwjs_DATA = js/cherokee.js

HTMLS = \
index.html

install-data-local: $(HTMLS)
	@$(mkinstalldirs) $(DESTDIR)$(cherokeewwwdir)
	@if test -f $(DESTDIR)$(cherokeewwwdir)/index.html ; then \
		echo "$@ will not overwrite existing $(cherokeewwwdir)/index.html"; \
	else \
		$(INSTALL_DATA) $(top_srcdir)/www/index.html $(DESTDIR)$(cherokeewwwdir)/index.html; \
	fi

uninstall-local:
	@if test -f $(DESTDIR)$(cherokeewwwdir)/index.html ; then \
		echo "rm -f $(DESTDIR)$(cherokeewwwdir)/index.html"; \
		$(RM) -f $(DESTDIR)$(cherokeewwwdir)/index.html; \
	fi


EXTRA_DIST = \
$(HTMLS) \
$(cherokeewwwcss_DATA) \
$(cherokeewwwjs_DATA) \
$(cherokeewwwimages_DATA)
