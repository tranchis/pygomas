import asyncio
import json
from datetime import datetime, timedelta

from .config import PERFORMATIVE, PERFORMATIVE_INFORM, NAME, ACTION, DESTROY
from .pack import Pack, PACK_MEDICPACK, PACK_AUTODESTROY_TIMEOUT
from spade.behaviour import TimeoutBehaviour
from spade.message import Message

now = datetime.now


class MedicPack(Pack):

    async def setup(self):
        self.type = PACK_MEDICPACK
        timeout = now() + timedelta(seconds=PACK_AUTODESTROY_TIMEOUT)
        self.add_behaviour(self.AutoDestroyBehaviour(start_at=timeout))
        await super().setup()

    async def perform_pack_taken(self, content):
        await self.stop()

    class AutoDestroyBehaviour(TimeoutBehaviour):
        async def run(self):
            msg = Message(to=self.agent.manager)
            msg.set_metadata(PERFORMATIVE, PERFORMATIVE_INFORM)
            content = {
                NAME: self.agent.name,
                ACTION: DESTROY
            }
            msg.body = json.dumps(content)
            await self.send(msg)
            await asyncio.sleep(1)
            await self.agent.stop()
