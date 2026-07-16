# -*- coding: utf-8; -*-
# This file is part of Superdesk.
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license
#
# Author  : amarwood_aap_com_au
# Creation: 2026-05-11 12:48
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo import UpdateOne
from superdesk.commands.data_updates import BaseDataUpdate


from newsroom.users import UsersService

from eve.utils import config


class DataUpdate(BaseDataUpdate):
    resource = "topics"
    use_async_resources = True

    async def forwards(
        self, collection: AsyncIOMotorCollection, database: AsyncIOMotorDatabase
    ) -> None:
        updates = []
        service = UsersService()
        users_list = await service.get_all_raw_as_list()

        async for topic in collection.find({}):
            user_id = topic.get("user")
            user = next((u for u in users_list if u.get("_id") == user_id), None)
            if not user:
                print(f"User id {user_id} does not exist!!!")
                continue

            update = {}

            # Already done
            old_subscribers = topic.get("subscribers")
            subscribers_is_list_of_dicts = isinstance(old_subscribers, list) and all(
                isinstance(item, dict) for item in old_subscribers
            )
            if not subscribers_is_list_of_dicts:
                update["subscribers"] = (
                    [{"user_id": user_id, "notification_type": "real-time"}]
                    if topic.get("notifications")
                    else []
                )

            if user and user.get("company"):
                update["company"] = user.get("company")
            else:
                print(f"No Company for user {user_id}")
                continue

            if "original_creator" not in topic:
                update["original_creator"] = user_id
            if "version_creator" not in topic:
                update["version_creator"] = user_id
            if "is_global" not in topic:
                update["is_global"] = topic.get("is_global", False)

            updates.append(
                UpdateOne(
                    {config.ID_FIELD: topic.get(config.ID_FIELD)},
                    {
                        "$set": update,
                        "$unset": {"notifications": ""},
                    },
                )
            )

            if len(updates) >= 500:
                print(f" 5 Type of collection: {type(collection)}")
                print(f" 5 Type of database: {type(database)}")
                await collection.bulk_write(updates)
                updates = []

        print(f"Type of collection: {type(collection)}")
        print(f"Type of database: {type(database)}")
        if updates:
            await collection.bulk_write(updates)

    async def backwards(
        self, collection: AsyncIOMotorCollection, database: AsyncIOMotorDatabase
    ) -> None:
        raise NotImplementedError()
