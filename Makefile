.PHONY: localecompile localegen

localecompile:
	cd pretix_guestlist && django-admin compilemessages

localegen:
	cd pretix_guestlist && django-admin makemessages -l de -l en
