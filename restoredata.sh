gunzip db-05-09-2023.json.gz
heroku run python manage.py flush
heroku run  python manage.py shell
from django.contrib.contenttypes.models import ContentType
ContentType.objects.all().delete()
exit()
heroku run python manage.py loaddata datatest.json
