#/bin/bash

mamba activate agria_server_env

exec gunicorn -w 4 -b 0.0.0.0:5000 run:app