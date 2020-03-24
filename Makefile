upload:
	@rm -rf build
	@rm -rf dist
	@sudo rm -rf sewer.egg-info
	@python setup.py sdist
	@python setup.py bdist_wheel
	@twine upload dist/* -r testpypi
	@pip3 install -U -i https://testpypi.python.org/pypi sewer


VERSION_STRING=$$(cat sewer/__version__.py | grep "__version__" | sed -e 's/__version__//g' | sed -e 's/=//' | sed -e 's/,//g' | sed -e 's/"//g' | sed -e 's/ //g')
uploadprod:
	@rm -rf build
	@rm -rf dist
	@sudo rm -rf sewer.egg-info
	@python setup.py sdist
	@python setup.py bdist_wheel
	@twine upload dist/*
	@printf "\n creating git tag: $(VERSION_STRING) \n"
	@printf "\n with commit message, see Changelong: https://github.com/komuw/sewer/blob/master/CHANGELOG.md \n" && git tag -a "$(VERSION_STRING)" -m "see Changelong: https://github.com/komuw/sewer/blob/master/CHANGELOG.md"
	@printf "\n git push the tag::\n" && git push --all -u --follow-tags
	@pip install -U sewer


# you can run single testcase as;
# 1. python -m unittest sewer.tests.test_Client.TestClient.test_something
# 2. python -m unittest discover -k test_find_dns_zone_id
test:
	@printf "\n removing pyc files::\n" && find . -type f -name *.pyc -delete | echo
	@printf "\n coverage erase::\n" && coverage erase
	@printf "\n coverage run::\n" && coverage run --omit="*tests*,*.virtualenvs/*,*.venv/*,*__init__*,*/usr/local/lib/python2.7/dist-packages*" -m unittest discover
	@printf "\n coverage report::\n" && coverage report --show-missing --fail-under=85
	@printf "\n run black::\n" && black --line-length=100 --py36 .
	@printf "\n run pylint::\n" && pylint --enable=E --disable=W,R,C --unsafe-load-any-extension=y sewer/


