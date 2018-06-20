# example-django-issue-tracker
Example project in django - Issue Tracker

[![Build Status](https://travis-ci.org/BrnoPCmaniak/example-django-issue-tracker.svg?branch=master)](https://travis-ci.org/BrnoPCmaniak/example-django-issue-tracker)


## How to start
```bash
docker-compose up
docker-compose run --rm web migrate --noinput
docker-compose run --rm web createsuperuser
```

How to start without docker
```bash
pip3 install -r requirements.txt
python3 issue_tracker/manage.py migrate
python3 issue_tracker/manage.py createsuperuser
python3 issue_tracker/manage.py runserver 0.0.0.0:8080
```

**The project is now available at [http://127.0.0.1:8080](http://127.0.0.1:8080)**

## How to use this software

After you create your account via command line you should head into
[http://127.0.0.1:8080/admin](http://127.0.0.1:8080/admin) section and create
new accounts as you need. In this project there are two roles of users.

1) **Superusers** *(have flag `is_superuser=True` on model)*
    - The superusers can change, create and delete issues.
2) **Staff users**
    - The staff users can only view issues be assigned to them and mark issues on which
are they assigned as done.

Also you can here create categories for the issues.

After this you can use this issue tracker according to your needs.
