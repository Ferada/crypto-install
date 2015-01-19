all: check test build/crypto-install

run: build/crypto-install
	build/crypto-install

check:
	pep8 .

test:
	./setup.py test

build:
	mkdir build

build/crypto-install: crypto-install build locale/*/LC_MESSAGES/crypto-install.mo
	sed \
		-e "s/GIT-TAG/`git describe --abbrev=0 --tags`/g" \
		-e "s/GIT-COMMIT/`git rev-parse --short=7 HEAD`/g" \
		-e "s/GIT-BRANCH/`git rev-parse --abbrev-ref HEAD`/g" \
		crypto-install > build/crypto-install
	chmod a+rx build/crypto-install

locale/*/LC_MESSAGES/crypto-install.mo: locale/*/LC_MESSAGES/crypto-install.po
	msgfmt $<

clean:
	rm -rf build
