import gc
import json
import os

import psutil
from django.core.files.base import ContentFile
from django.core.management import BaseCommand

from core.models import Leak


class Command(BaseCommand):

    def run_iteration(self, payload):
        raw = json.dumps(payload)
        process = psutil.Process(os.getpid())
        memory_start = process.memory_full_info().rss / 1024 ** 2
        leak = Leak.objects.create(f=ContentFile(raw.encode(), "leak"), f_json=payload)
        for i in range(100):
            # print(process.memory_full_info().rss / 1024 ** 2)
            new = Leak.objects.get(id=leak.id)
            extra = {"f": new.f}
        memory_end = process.memory_full_info().rss / 1024 ** 2
        memory_diff = memory_end - memory_start
        print(f"{list(payload.keys())[0]}, {memory_start=}MB, {memory_end=}MB,  {memory_diff=}MB")

    def handle(self, *args, **options):
        payloads = {
            "1kb": "b" * 1 * 1024,
            "10kb": "b" * 10 * 1024,
            "100kb": "b" * 100 * 1024,
            "1mb": "b" * 1 * 1024 * 1024,
            "10mb": "b" * 10 * 1024 * 1024,
            "100mb": "b" * 100 * 1024 * 1024,
        }
        for key, value in payloads.items():
            self.run_iteration({key: value})
            gc.collect()

