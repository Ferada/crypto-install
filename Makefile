all: build
	@sed \
		-e "s/GIT-TAG/`git describe --abbrev=0 --tags`/g" \
		-e "s/GIT-COMMIT/`git rev-parse --short=7 HEAD`/g" \
		-e "s/GIT-BRANCH/`git rev-parse --abbrev-ref HEAD`/g" \
		crypto-install.py > build/crypto_install.py

build:
	mkdir build
