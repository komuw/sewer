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
upload: upload_only
	@${pip} install -U -i https://testpypi.python.org/pypi sewer

upload_only:
	@rm -rf build
	@rm -rf dist
	@rm -rf sewer.egg-info
	@${python} setup.py sdist
	@${python} setup.py bdist_wheel
	@${twine} upload dist/* -r testpypi


uploadprod: uploadprod_only uploadprod_tag
	@${pip} install -U sewer

uploadprod_only:
	@rm -rf build
	@rm -rf dist
	@sudo rm -rf sewer.egg-info
	@${python} setup.py sdist
	@${python} setup.py bdist_wheel
	@${twine} upload dist/*

uploadprod_tag:
	@printf "\n creating git tag: $(VERSION_STRING) \n"
	@printf "\n with commit message, see Changelong: https://github.com/komuw/sewer/blob/master/CHANGELOG.md \n" && git tag -a "$(VERSION_STRING)" -m "see Changelong: https://github.com/komuw/sewer/blob/master/CHANGELOG.md"
	@printf "\n git push the tag::\n" && git push --all -u --follow-tags


# you can run single testcase as;
# 1. python -m unittest sewer.tests.test_Client.TestClient.test_something
# 2. python -m unittest discover -k test_find_dns_zone_id

.PHONY: test testdata rsatestkeys secptestkeys

test:
	@printf "\n removing pyc files::\n" && find . -type f -name *.pyc -delete | echo
	@printf "\n coverage erase::\n" && ${coverage} erase
	@printf "\n coverage run::\n" && ${coverage} run --omit="*tests*,*.virtualenvs/*,*.venv/*,*__init__*" -m unittest discover
	@printf "\n coverage report::\n" && ${coverage} report --show-missing --fail-under=85
	@printf "\n run black::\n" && ${black} --line-length=100 --target-version py35 .
	@printf "\n run pylint::\n" && ${pylint} --enable=E --disable=W,R,C --unsafe-load-any-extension=y sewer/


testdata: rsatestkeys secptestkeys

rsatestkeys:
	openssl genpkey -out test/rsa2048.pem -algorithm RSA -pkeyopt rsa_keygen_bits:2048
	openssl genpkey -out test/rsa3072.pem -algorithm RSA -pkeyopt rsa_keygen_bits:3072
	openssl genpkey -out test/rsa4096.pem -algorithm RSA -pkeyopt rsa_keygen_bits:4096

secptestkeys:
	openssl genpkey -out test/secp256r1.pem -algorithm EC -pkeyopt ec_paramgen_curve:P-256
	openssl genpkey -out test/secp384r1.pem -algorithm EC -pkeyopt ec_paramgen_curve:P-384
# not actually useful with LE at this time
#	openssl genpkey -out test/secp521r1.pem -algorithm EC -pkeyopt ec_paramgen_curve:P-521
