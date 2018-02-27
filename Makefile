upload:
	@rm -rf build
	@rm -rf dist
	@sudo rm -rf sewer.egg-info
	@python setup.py sdist
	@python setup.py bdist_wheel
	@twine upload dist/* -r testpypi
	@sudo pip3 install -U -i https://testpypi.python.org/pypi sewer

uploadprod:
	@rm -rf build
	@rm -rf dist
	@sudo rm -rf sewer.egg-info
	@python setup.py sdist
	@python setup.py bdist_wheel
	@twine upload dist/*
	@sudo pip3 install -U sewer

test:
	@printf "\n removing pyc files::\n" && find . -type f -name *.pyc -delete | echo
	@printf "\n coverage erase::\n" && coverage erase
	@printf "\n coverage run::\n" && coverage run --omit="*tests*,*.virtualenvs/*,*.venv/*,*__init__*,*/usr/local/lib/python2.7/dist-packages*" -m unittest discover
	@printf "\n coverage report::\n" &&coverage report --show-missing --fail-under=85
	@printf "\n run flake8::\n" && flake8 .
	@printf "\n run pylint::\n" && pylint --enable=E --disable=W,R,C sewer/
