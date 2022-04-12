# Possible FileField (FieldFile) memory leak?

[Existing ticket](https://code.djangoproject.com/ticket/16022)

Observations:

- I think that accessing a FileField descriptor for a model instance causes a memory leak.
- A leak is most noticable if the instance happens to contain a field with a large amount of data on it (a large text field, json field, etc)
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

See the [tests](leak/core/tests.py) for working code.

```bash
git clone git@github.com/massover/leak.git
cd leak
pip install -r requirements.txt
./manage.py test
```

```bash
test no patch
memory_start=71.26171875, memory_end=631.640625,  memory_diff=560.37890625
.test with patch
memory_start=641.67578125, memory_end=681.9609375,  memory_diff=40.28515625
```

Solutions?

- I'm no [weakref.proxy](https://docs.python.org/3/library/weakref.html#weakref.proxy) expert, but this is what it's for? I did run this code against the django test suite and it passed. No idea about compatibility.

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

