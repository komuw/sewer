# we may need something other than the system default here
# use  $ PYTHON=python3 make ...  for example
python = python
ifdef PYTHON
	python = ${PYTHON}
endif

# invoke these using  ${python} -m  to avoid yet more xxxx3 naming issues
twine = ${python} -m twine
pip = ${python} -m pip
coverage = ${python} -m coverage
black = ${python} -m black
pylint = ${python} -m pylint


VERSION_STRING=$$(sed -n -e '/"version"/ s/.*version": *"\([^"]*\)".*/\1/p' <sewer/meta.json)


# foo is just a show-me target
foo:
	@echo "VERSION = ${VERSION_STRING}"
	@echo "python is ${python}"
	@echo "pip command: ${pip}"
	@echo "twine command: ${twine}"
	@echo "coverage command: ${coverage}"
	@echo "black command: ${black}"
	@echo "pylint command: ${pylint}"


# upload to testpypi
upload: build
	@${twine} upload dist/* -r testpypi
	@${pip} install -U -i https://testpypi.python.org/pypi sewer

build:
	@rm -rf build
	@rm -rf dist
	@rm -rf sewer.egg-info
	@${python} setup.py sdist
	@${python} setup.py bdist_wheel

uploadprod: build uploadprod_only uploadprod_tag
	@${pip} install -U sewer

uploadprod_only:
	@${twine} upload dist/*

uploadprod_tag:
	@printf "\n creating git tag: $(VERSION_STRING) \n"
	@printf "\n with commit message, see Changelong: https://github.com/komuw/sewer/blob/master/CHANGELOG.md \n" && git tag -a "$(VERSION_STRING)" -m "see Changelong: https://github.com/komuw/sewer/blob/master/CHANGELOG.md"
	@printf "\n git push the tag::\n" && git push --all -u --follow-tags


# you can run single testcase as;
# 1. python -m unittest sewer.tests.test_Client.TestClient.test_something
# 2. python -m unittest discover -k test_find_dns_zone_id

TDATA = tests/data

.PHONY: clean coverage format lint

test: testdata coverage format lint

testdata: rsatestkeys secptestkeys

coverage: clean
	@printf "\n coverage erase::\n" && ${coverage} erase
	@printf "\n coverage run::\n" && ${coverage} run 
	@printf "\n coverage report::\n" && ${coverage} report --show-missing --fail-under=85

clean:
	@printf "\n removing pyc files::\n" && find . -type f -name *.pyc -delete | echo

format:
	@printf "\n run black::\n" && ${black} .

lint:
	@printf "\n run pylint::\n" && ${pylint} --enable=E --disable=W,R,C --unsafe-load-any-extension=y sewer/

rsatestkeys: ${TDATA}/rsa2048.pem ${TDATA}/rsa3072.pem ${TDATA}/rsa4096.pem

${TDATA}/rsa2048.pem:
	openssl genpkey -out ${TDATA}/rsa2048.pem -algorithm RSA -pkeyopt rsa_keygen_bits:2048

${TDATA}/rsa3072.pem:
	openssl genpkey -out ${TDATA}/rsa3072.pem -algorithm RSA -pkeyopt rsa_keygen_bits:3072

${TDATA}/rsa4096.pem:
	openssl genpkey -out ${TDATA}/rsa4096.pem -algorithm RSA -pkeyopt rsa_keygen_bits:4096

secptestkeys: ${TDATA}/secp256r1.pem ${TDATA}/secp384r1.pem

${TDATA}/secp256r1.pem:
	openssl genpkey -out ${TDATA}/secp256r1.pem -algorithm EC -pkeyopt ec_paramgen_curve:P-256

${TDATA}/secp384r1.pem:
	openssl genpkey -out ${TDATA}/secp384r1.pem -algorithm EC -pkeyopt ec_paramgen_curve:P-384

# not actually useful with LE at this time
${TDATA}/secp521r1.pem:
	openssl genpkey -out ${TDATA}/secp521r1.pem -algorithm EC -pkeyopt ec_paramgen_curve:P-521
