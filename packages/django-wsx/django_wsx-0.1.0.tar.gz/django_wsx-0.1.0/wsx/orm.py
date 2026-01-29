from __future__ import annotations
from asgiref.sync import sync_to_async


class ORM:
    def __init__(self, model):
        self.model = model
        self.qs = model.objects.all()

    def filter(self, **kwargs):
        self.qs = self.qs.filter(**kwargs)
        return self

    def select_related(self, *args):
        self.qs = self.qs.select_related(*args)
        return self

    def order_by(self, *args):
        self.qs = self.qs.order_by(*args)
        return self

    def limit(self, n: int):
        self.qs = self.qs[:n]
        return self

    async def all(self):
        return await sync_to_async(list)(self.qs)

    async def first(self):
        return await sync_to_async(self.qs.first)()

    async def get(self, **kwargs):
        return await sync_to_async(self.model.objects.get)(**kwargs)

    async def create(self, **kwargs):
        return await sync_to_async(self.model.objects.create)(**kwargs)

    async def update(self, **kwargs):
        return await sync_to_async(self.qs.update)(**kwargs)

    async def delete(self):
        return await sync_to_async(self.qs.delete)()