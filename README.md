# Possible FileField (FieldFile) memory optimization?

[Existing ticket](https://code.djangoproject.com/ticket/16022)

Observations:

- I think that accessing a FileField descriptor for a model instance ~causes a memory leak~ can use a memory optimization.
- A memory difference (from garbage) is most noticable if the instance happens to contain a field with a large amount of data on it (a large text field, json field, etc)
- I believe it's a reference cycle between a model instance.file_field and FileField.instance
- I believe that the reference cycles are subject to whenever the gc wants to collect. In the tests below, that means `memory_end` depends on the gc timing.


Minimal code to reproduce can look like the following.

```python
from django.db import models
from django.db.models import JSONField

class Leak(models.Model):
    f = models.FileField()
    f_json = JSONField()
    
def get_f(id):
    leak = Leak.objects.get(id=1)
    return leak.f
```

See the [management command](https://github.com/massover/possible-leak/blob/main/core/management/commands/leak.py) for working code.

## Steps to repro

```bash
git clone git@github.com/massover/leak.git
cd leak
pip install -r requirements.txt
./manage.py migrate
./manage.py leak
./manage.py leak --patch
pip uninstall django
pip install git+https://github.com/massover/django.git@issues/16022

# to run it again against a live version and see the leak
pip uninstall django
pip install django
./manage.py leak
```

```bash
# unpatched
# ./manage.py leak
1kb, memory_start=150.703125MB, memory_end=150.953125MB,  memory_diff=0.25MB
10kb, memory_start=151.09375MB, memory_end=151.96875MB,  memory_diff=0.875MB
100kb, memory_start=152.71875MB, memory_end=160.46875MB,  memory_diff=7.75MB
1mb, memory_start=172.09375MB, memory_end=249.921875MB,  memory_diff=77.828125MB
10mb, memory_start=387.453125MB, memory_end=818.171875MB,  memory_diff=430.71875MB
100mb, memory_start=2121.34375MB, memory_end=5338.34375MB,  memory_diff=3217.0MB
```

```bash
# patched
# ./manage.py leak --patch
1kb, memory_start=148.90625MB, memory_end=149.0625MB,  memory_diff=0.15625MB
10kb, memory_start=149.203125MB, memory_end=149.265625MB,  memory_diff=0.0625MB
100kb, memory_start=150.84375MB, memory_end=151.875MB,  memory_diff=1.03125MB
1mb, memory_start=166.234375MB, memory_end=181.765625MB,  memory_diff=15.53125MB
10mb, memory_start=319.25MB, memory_end=319.359375MB,  memory_diff=0.109375MB
100mb, memory_start=1623.28125MB, memory_end=1623.4375MB,  memory_diff=0.15625MB
```

```bash
# unpatched @ issues/16022
# ./manage.py leak
1kb, memory_start=149.21875MB, memory_end=149.359375MB,  memory_diff=0.140625MB
10kb, memory_start=149.5MB, memory_end=149.640625MB,  memory_diff=0.140625MB
100kb, memory_start=151.234375MB, memory_end=151.90625MB,  memory_diff=0.671875MB
1mb, memory_start=166.234375MB, memory_end=182.859375MB,  memory_diff=16.625MB
10mb, memory_start=320.421875MB, memory_end=320.5MB,  memory_diff=0.078125MB
100mb, memory_start=1624.140625MB, memory_end=1624.203125MB,  memory_diff=0.0625MB
```

Solutions?

- I'm no [weakref.proxy](https://docs.python.org/3/library/weakref.html#weakref.proxy) expert, but this is what it's for? I ran this code against the django test suite and it passed. No idea about compatibility.

```python
class FieldFile(File):
    def __init__(self, instance, field, name):
        super().__init__(None, name)
        self.instance = weakref.proxy(instance)
        self.field = field
        self.storage = field.storage
        self._committed = True
    ...
```

