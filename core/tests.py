import io
import os
import json
import unittest

import psutil
from django.core.files.base import ContentFile
from django.db.models.fields.files import FieldFile
from django.test import TestCase

from core.models import Leak, get_f


class TestLeak(TestCase):
    def test_it(self):
        print("test no patch")
        data = {"10mb":"b"*10*1024*1024}
        raw = json.dumps(data)
        process = psutil.Process(os.getpid())
        memory_start = process.memory_full_info().rss / 1024 ** 2
        leak = Leak.objects.create(f=ContentFile(raw.encode(), "leak"), f_json=data)
        for i in range(100):
            # print(process.memory_full_info().rss / 1024 ** 2)
            new = Leak.objects.get(id=leak.id)
            extra = {"f": new.f}
        memory_end = process.memory_full_info().rss / 1024 ** 2
        memory_diff = memory_end - memory_start
        print(f"{memory_start=}, {memory_end=},  {memory_diff=}")
        assert new.f.read() == leak.f.read()

    def test_get_f(self):
        leak = Leak.objects.create(f=ContentFile("example".encode(), "leak"), f_json="example")
        f = get_f(leak.id)
        new = io.StringIO("some initial text data")
        f.save("new-name", new)



class TestPatch(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = FieldFile.__init__
        import weakref
        def __init__(self, instance, field, name):
            super(FieldFile, self).__init__(None, name)
            self.instance = weakref.proxy(instance)
            self.field = field
            self.storage = field.storage
            self._committed = True
        FieldFile.__init__ = __init__

    @classmethod
    def tearDownClass(cls):
        FieldFile.__init__ = cls.original

    def test_with_patch(self):
        print("test with patch")
        data = {"10mb": "b" * 10 * 1024 * 1024}
        raw = json.dumps(data)
        process = psutil.Process(os.getpid())
        memory_start = process.memory_full_info().rss / 1024 ** 2
        leak = Leak.objects.create(f=ContentFile("leak", raw.encode()), f_json=data)
        for i in range(100):
            # print(process.memory_full_info().rss / 1024 ** 2)
            new = Leak.objects.get(id=leak.id)
            extra = {"f": new.f}
        memory_end = process.memory_full_info().rss / 1024 ** 2
        memory_diff = memory_end - memory_start
        print(f"{memory_start=}, {memory_end=},  {memory_diff=}")
        assert new.f.read() == leak.f.read()

    def test_get_f(self):
        leak = Leak.objects.create(f=ContentFile("example".encode(), "leak"), f_json="example")
        f = get_f(leak.id)
        new = io.StringIO("some initial text data")
        f.save("new-name", new)
