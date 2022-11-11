import gc
import json
import os

import psutil
import weakref
from django.core.files.base import ContentFile
from django.core.management import BaseCommand
from django.db.models.fields.files import FieldFile

from core.models import Leak


class Command(BaseCommand):

    def add_arguments(self, parser):
        # Positional arguments
        # Named (optional) arguments
        parser.add_argument(
            '--patch',
            action='store_true',
            default=False,
        )

    def patch(self, patch):
        if not patch:
            return

        def __init__(self, instance, field, name):
            super(FieldFile, self).__init__(None, name)
            self.instance = weakref.proxy(instance)
            self.field = field
            self.storage = field.storage
            self._committed = True

        FieldFile.__init__ = __init__

    def run_iteration(self, payload, process):
        raw = json.dumps(payload)
        leak = Leak.objects.create(f=ContentFile(raw.encode(), "leak"), f_json=payload)
        memory_start = process.memory_full_info().rss / 1024 ** 2
        for i in range(100):
            new = Leak.objects.get(id=leak.id)
            extra = {"f": new.f}
        return memory_start


    def handle(self, *args, **options):
        self.patch(options["patch"])
        process = psutil.Process(os.getpid())
        payloads = {
            "1kb": "b" * 1 * 1024,
            "10kb": "b" * 10 * 1024,
            "100kb": "b" * 100 * 1024,
            "1mb": "b" * 1 * 1024 * 1024,
            "10mb": "b" * 10 * 1024 * 1024,
            "100mb": "b" * 100 * 1024 * 1024,
        }
        for key, value in payloads.items():
            payload = {key: value}
            # at the end of the `run_iterantion` method call, with a weak ref, the FieldFile
            # should be garbage collected. Without a weak ref, it's a cyclic reference
            # so it remains in memory.
            memory_start = self.run_iteration(payload, process)
            memory_end = process.memory_full_info().rss / 1024 ** 2
            memory_diff = memory_end - memory_start
            print(f"{list(payload.keys())[0]}, {memory_start=}MB, {memory_end=}MB,  {memory_diff=}MB")
            gc.collect()

