# example-django-issue-tracker
Example project in django - Issue Tracker


How to start
```
docker-compose up
docker-compose run --rm web migrate --noinput
docker-compose run --rm web createsuperuser
```

How to start without docker
```
pip3 install -r requirements.txt
python3 issue_tracker/manage.py migrate
python3 issue_tracker/manage.py createsuperuser
python3 issue_tracker/manage.py runserver 0.0.0.0:8080
```

**The project is now availible at [http://127.0.0.1:8080](http://127.0.0.1:8080)**
