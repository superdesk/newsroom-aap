# -*- coding: utf-8; -*-
# This file is part of Superdesk.
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license
#
# Author  : amarwood_aap_com_au
# Creation: 2026-05-13 11:58

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from superdesk.commands.data_updates import BaseDataUpdate


class DataUpdate(BaseDataUpdate):
    resource = "users"
    use_async_resources = True

    async def forwards(self, collection: AsyncIOMotorCollection, database: AsyncIOMotorDatabase) -> None:
        await collection.update_many({}, {"$set": {"locale": "en"}})

    async def backwards(self, collection: AsyncIOMotorCollection, database: AsyncIOMotorDatabase) -> None:
        raise NotImplementedError()
