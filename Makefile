clean:
	find . -name "*.pyc" -delete

list_updates:
	pip list -lo

test:
	export PYTHONPATH=$$PYTHONPATH:`pwd`/crawler; \
	py.test --capture=sys -s -x \
		--doctest-modules \
		--looponfail \
		--pep8 crawler tests

## --showlocals sometimes added for more details
