upload:
	@rm -rf build
	@rm -rf dist
	@python setup.py sdist
	@python setup.py bdist_wheel
	@twine upload dist/* -r testpypi
	@twine upload dist/*
	@sudo pip install -U sewer
