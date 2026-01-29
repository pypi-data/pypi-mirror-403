from __future__ import annotations


class Groups:
    def __init__(self, consumer):
        self.consumer = consumer
        self.layer = consumer.channel_layer

    async def join(self, group: str):
        await self.layer.group_add(group, self.consumer.channel_name)

    async def leave(self, group: str):
        await self.layer.group_discard(group, self.consumer.channel_name)

    async def broadcast(self, group: str, *, action: str, data: dict):
        # Channels converts dots to underscores for handler method name
        await self.layer.group_send(group, {"type": "wsx.group", "action": action, "data": data})