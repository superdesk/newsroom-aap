from newsroom import Resource
from content_api.items.resource import schema


class AAPReleaseResource(Resource):
    resource_title = 'Press Release Service'
    endpoint_name = 'releases'
    datasource = {
        'search_backend': 'elastic',
        'source': 'items',
        'default_sort': [('versioncreated', -1)],
        'elastic_filter': {
            "bool": {
                "must": [
                    {
                        "term": {
                            "service.code": {
                                "value": "j"
                            }
                        }
                    },
                    {
                        "terms": {
                            "source": [
                                "PRN",
                                "GlobeNewswire"
                            ]
                        }
                    },
                    {
                        "term": {
                            "pubstatus": {
                                "value": "usable"
                            }
                        }
                    },
                    {
                      "range": {
                        "versioncreated": {
                          "gte": "now-90d"
                        }
                      }
                    }
                ]
            }
        },
        'projection': {
            '_id': 1,
            'headline': 1,
            'body_html': 1,
            'versioncreated': 1,
            'extra': 1,
            'description_html': 1,
            'source:': 1,
            'service': 1,
            'anpa_category': 1
        },
        'schema': schema
    }
    item_url = r'regex("[\w.:_-]+")'
    item_methods = ['GET']
    resource_methods = ['GET']
    internal_resource = True
