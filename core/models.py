from django.db import models
from django.db.models import JSONField


def upload_to_fn(instance, filename):
    return f"{instance.id}.json"


class Leak(models.Model):
    f = models.FileField(upload_to=upload_to_fn)
    f_json = JSONField()


def get_f(id):
    return Leak.objects.get(id=id).f
