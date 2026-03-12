Feature: News API AAP-RSS Feed

  Background: Initial setup
    Given "companies"
        """
        [{"name": "Test Company", "is_enabled" : true}]
        """
    Given "news_api_tokens"
        """
        [{"company" : "#companies._id#", "enabled" : true}]
        """
    When we save API token

  Scenario: Simple aap rss request
    Given "products"
        """
        [{"name": "A fishy Product",
        "description": "a product for those interested in fish",
        "companies" : [
          "#companies._id#"
        ],
        "query": "fish",
        "product_type": "news_api"
        },
        {"name": "A pic product",
        "decsription": "pic product",
        "companies" : [
          "#companies._id#"
        ],
        "query": "",
        "sd_product_id": "1",
        "product_type": "news_api"
        }]
        """
    Given "items"
        """
        [{"_id":"urn-1234567890",
        "body_html": "<p>Once upon a time there was a fish who could swim</p>", "headline": "headline 1",
        "byline": "S Smith", "pubstatus": "usable", "service" : [{"name" : "Australian General News", "code" : "a"}],
        "description_text": "summary",
        "associations" : {
            "featuremedia" : {
                "mimetype" : "image/jpeg",
                "description_text" : "Deputy Prime Minister Michael McCormack during Question Time",
                "version" : "1",
                "byline" : "Mick Tsikas/AAP PHOTOS",
                "body_text" : "QUESTION TIME ALT",
                "products": [{"code": "1"}],
                "renditions" : {
                    "16-9" : {
                        "href" : "/assets/5fc5dce16369ab07be3325fa",
                        "height" : 720,
                        "width" : 1280,
                        "media" : "5fc5dce16369ab07be3325fa",
                        "poi" : {
                            "x" : 453,
                            "y" : 335
                        },
                        "mimetype" : "image/jpeg"
                    }
            }
        }},
         "firstpublished": "#DATE-1#", "versioncreated": "#DATE-1#"}]
        """
    When we get "aap-rss"
    Then we get OK response
    Then we "get" "<title>headline 1</title>" in rss xml response
    Then we "get" "<media:credit>Mick Tsikas/AAP PHOTOS</media:credit>" in rss xml response


  Scenario: A story maintains its original link
    Given "products"
        """
        [{"name": "A fishy Product",
        "description": "a product for those interested in fish",
        "companies" : [
          "#companies._id#"
        ],
        "query": "fish",
        "product_type": "news_api"
        },
        {"name": "A pic product",
        "decsription": "pic product",
        "companies" : [
          "#companies._id#"
        ],
        "query": "",
        "sd_product_id": "1",
        "product_type": "news_api"
        }]
        """
    Given "items"
        """
        [{"_id":"urn-1234567890",
        "body_html": "<p>Once upon a time there was a fish who could swim</p>", "headline": "headline 1",
        "byline": "S Smith", "pubstatus": "usable", "service" : [{"name" : "Australian General News", "code" : "a"}],
        "description_text": "summary",
         "firstpublished": "#DATE-1#", "versioncreated": "#DATE-1#",
         "nextversion": "urn-1234567891"},
         {"_id":"urn-1234567891",
        "body_html": "<p>Story with a totaly different headline, still about fish</p>", "headline": "headline 2",
        "byline": "S Smith", "pubstatus": "usable", "service" : [{"name" : "Australian General News", "code" : "a"}],
        "description_text": "summary",
         "firstpublished": "#DATE#", "versioncreated": "#DATE#",
         "evolved_from": "urn-1234567890",
         "ancestors": ["urn-1234567890"]}
         ]
        """
    When we get "aap-rss"
    Then we get OK response
    Then we "get" "<link>https://aapnews.aap.com.au/news/headline-1</link>" in rss xml response

  Scenario: A story killed
    Given "products"
        """
        [{"name": "A fishy Product",
        "description": "a product for those interested in fish",
        "companies" : [
          "#companies._id#"
        ],
        "query": "fish",
        "product_type": "news_api"
        },
        {"name": "A pic product",
        "decsription": "pic product",
        "companies" : [
          "#companies._id#"
        ],
        "query": "",
        "sd_product_id": "1",
        "product_type": "news_api"
        }]
        """
    Given "items"
        """
        [{"_id":"urn-1234567890",
        "body_html": "<p>Once upon a time there was a fish who could swim</p>", "headline": "headline 1",
        "byline": "S Smith", "pubstatus": "canceled", "service" : [{"name" : "Australian General News", "code" : "a"}],
        "description_text": "summary",
         "firstpublished": "#DATE-1#", "versioncreated": "#DATE-1#", "_current_version": 1}
         ]
        """
    Given "items_versions"
        """
        [
        {"_id_document":"urn-1234567890",
        "body_html": "<p>Once upon a time there was a fish who could swim</p>", "headline": "updated headline 1",
        "byline": "S Smith", "pubstatus": "canceled", "service" : [{"name" : "Australian General News", "code" : "a"}],
        "description_text": "summary",
         "firstpublished": "#DATE-1#", "versioncreated": "#DATE-1#", "_current_version": 2},
        {"_id_document":"urn-1234567890",
        "body_html": "<p>Once upon a time there was a fish who could swim</p>", "headline": "headline 1",
        "byline": "S Smith", "pubstatus": "canceled", "service" : [{"name" : "Australian General News", "code" : "a"}],
        "description_text": "summary",
         "firstpublished": "#DATE-1#", "versioncreated": "#DATE-1#", "_current_version": 1}
         ]
        """
    When we get "aap-rss"
    Then we get OK response
    Then we "get" "<licensed_news:deleted>yes</licensed_news:deleted>" in rss xml response
    Then we "get" "<link>https://aapnews.aap.com.au/news/headline-1</link>" in rss xml response

  Scenario: A story corrected
    Given "products"
        """
        [{"name": "A fishy Product",
        "description": "a product for those interested in fish",
        "companies" : [
          "#companies._id#"
        ],
        "query": "fish",
        "product_type": "news_api"
        },
        {"name": "A pic product",
        "decsription": "pic product",
        "companies" : [
          "#companies._id#"
        ],
        "query": "",
        "sd_product_id": "1",
        "product_type": "news_api"
        }]
        """
    Given "items"
        """
        [{"_id":"urn-1234567890",
        "body_html": "<p>Once upon a time there was a fish who could swim</p>", "headline": "headline 2",
        "byline": "S Smith", "pubstatus": "usable", "service" : [{"name" : "Australian General News", "code" : "a"}],
        "description_text": "summary",
         "firstpublished": "#DATE-1#", "versioncreated": "#DATE#", "_current_version": 2}
         ]
        """
    Given "items_versions"
        """
        [{"_id_document":"urn-1234567890",
        "body_html": "<p>Once upon a time there was a fish who could swim</p>", "headline": "headline 1",
        "byline": "S Smith", "pubstatus": "usable", "service" : [{"name" : "Australian General News", "code" : "a"}],
        "description_text": "summary",
         "firstpublished": "#DATE-1#", "versioncreated": "#DATE-1#", "_current_version": 1}
         ]
        """
    When we get "aap-rss"
    Then we get OK response
    Then we "get" "<link>https://aapnews.aap.com.au/news/headline-1</link>" in rss xml response