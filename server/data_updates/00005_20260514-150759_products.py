# -*- coding: utf-8; -*-
# This file is part of Superdesk.
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license
#
# Author  : amarwood_aap_com_au
# Creation: 2026-05-14 15:07

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from superdesk.commands.data_updates import BaseDataUpdate
from bson import ObjectId
from pymongo import UpdateOne


class DataUpdate(BaseDataUpdate):
    resource = "products"
    use_async_resources = True

    async def forwards(
        self, collection: AsyncIOMotorCollection, database: AsyncIOMotorDatabase
    ) -> None:
        updates = []

        cursor = collection.find({"navigations.0": {"$exists": True}})

        async for product in cursor:
            original_navs = product.get("navigations", [])

            cleaned_navs = list(
                {
                    ObjectId(nav) if isinstance(nav, str) else nav
                    for nav in original_navs
                    if nav  # Ensure we don't try to convert None or empty strings
                }
            )

            if len(cleaned_navs) != len(original_navs) or any(
                isinstance(n, str) for n in original_navs
            ):
                updates.append(
                    UpdateOne(
                        {"_id": product["_id"]}, {"$set": {"navigations": cleaned_navs}}
                    )
                )

            # 4. Batch execution
            if len(updates) >= 500:
                await collection.bulk_write(updates)
                updates = []

        # 5. Final flush for the remaining documents
        if updates:
            await collection.bulk_write(updates)
            print(f"Successfully migrated navigations for {len(updates)} products.")

    async def backwards(
        self, collection: AsyncIOMotorCollection, database: AsyncIOMotorDatabase
    ) -> None:
        raise NotImplementedError()
