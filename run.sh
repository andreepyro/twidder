# NOTE: because of user session implementation, this application requires to run in one process (i.e. using one worker only)
gunicorn --workers 1 --threads 8 -b 0.0.0.0:8080 appserver:app
