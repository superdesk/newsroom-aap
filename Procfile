web: gunicorn -b 0.0.0.0:$PORT -w 3 newsroom.app:app
websocket: python -m newsroom.websocket
push: PUSH=1 gunicorn -b 0.0.0.0:$PORT -w 3 newsroom.app:app
