web: gunicorn -b 0.0.0.0:$PORT -w 3 newsroom.app:app
newsapi: gunicorn -b "0.0.0.0:${APIPORT:-$PORT}" -w 3 newsroom.news_api.app:app
websocket: python -m newsroom.websocket
push: PUSH=1 gunicorn -b 0.0.0.0:$PORT -w 3 newsroom.app:app
newsroom: celery -A newsroom.worker.celery -Q "${SUPERDESK_CELERY_PREFIX}newsroom" worker
beat: celery -A newsroom.worker.celery beat --pid=
