all: check test build/crypto-install.py

run: build/crypto-install.py
	build/crypto-install.py

check:
	pep8 .

test:
	./setup.py test

build:
	mkdir build

build/crypto-install.py: crypto-install.py build
	sed \
		-e "s/GIT-TAG/`git describe --abbrev=0 --tags`/g" \
		-e "s/GIT-COMMIT/`git rev-parse --short=7 HEAD`/g" \
		-e "s/GIT-BRANCH/`git rev-parse --abbrev-ref HEAD`/g" \
		crypto-install.py > build/crypto-install.py
	chmod a+rx build/crypto-install.py

clean:
	rm -rf build
