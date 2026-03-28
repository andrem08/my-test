source venv/bin/activate
flask db migrate -m "update or db"
flask db upgrade
