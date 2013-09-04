ENV=./.env
mkdir -p $ENV
virtualenv $ENV
source $ENV/bin/activate
pip install -U -r requirements.txt
./run_tests
