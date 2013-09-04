bootstrap:
	ENV=./.env
	mkdir -p $ENV
	virtualenv $ENV
	source $ENV/bin/activate
	pip install -U -r requirements.txt
	./run_tests

clean:
	find . -name "*.pyc" -delete

list_updates:
	pip list -lo

test:
	export PYTHONPATH=$PYTHONPATH:`pwd`/src/main
	py.test --capture=sys -s -x \
		--doctest-modules \
		--looponfail \
		--pep8 src/main src/test

	# --showlocals sometimes added for more details
