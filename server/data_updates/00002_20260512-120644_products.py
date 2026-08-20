# -*- coding: utf-8; -*-
# This file is part of Superdesk.
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license
#
# Author  : amarwood_aap_com_au
# Creation: 2026-05-12 12:06
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from superdesk.commands.data_updates import BaseDataUpdate
from newsroom.companies import CompanyServiceAsync


class DataUpdate(BaseDataUpdate):
    resource = "products"
    use_async_resources = True

    async def forwards(
        self, collection: AsyncIOMotorCollection, database: AsyncIOMotorDatabase
    ) -> None:
        products = await collection.find({}).to_list(length=1000)
        companies = await CompanyServiceAsync().get_all_raw_as_list()
        for company in companies:
            update: dict[str, Any] = {}
            if "products" not in company:
                company_products = [
                    {"_id": p.get("_id"), "section": p.get("product_type"), "seats": 0}
                    for p in products
                    if p.get("companies")
                    and str(company["_id"]) in set(map(str, p["companies"]))
                ]
                update = {"products": company_products}

            if "embed_permissions" not in company:
                update["embed_permissions"] = {
                    "audio": ["display"],
                    "embed_code": ["display"],
                    "featuremedia": ["display"],
                    "picture": ["display"],
                    "sd_product": ["display"],
                    "video": ["display"],
                }

            if update:
                await CompanyServiceAsync().mongo_async.update_one(
                    {"_id": company.get("_id")}, {"$set": update}
                )

    async def backwards(
        self, collection: AsyncIOMotorCollection, database: AsyncIOMotorDatabase
    ) -> None:
        raise NotImplementedError()
