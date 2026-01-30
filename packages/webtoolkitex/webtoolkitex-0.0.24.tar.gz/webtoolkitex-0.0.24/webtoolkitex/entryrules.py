"""
Provide mechanism for URL rules:
  - some URLs require special handling, crawler
  - we may want to block certain domains
"""
from pathlib import Path
import re
import json


class EntryRules(object):
    """
    Entry rules
    """
    def __init__(self):
        """ Constructor """
        rules = [{
            "id": 3,
            "enabled": True,
            "rule_url": ".*reddit\\.com.*\\.json.*",
            "rule_name": "reddit",
            "block": False,
            "auto_tag": "",
            "browser": "HttpMorphCrawler"
        },
        {
            "id": 4,
            "enabled": True,
            "rule_url": ".*reddit\\.com.*\\.rss.*",
            "rule_name": "reddit",
            "block": False,
            "auto_tag": "",
            "browser": "HttpMorphCrawler"
        },
        {
            "id": 5,
            "enabled": True,
            "rule_url": ".*youtube\\.com.*",
            "rule_name": "youtube",
            "block": False,
            "auto_tag": "",
            "browser": "RequestsCrawler"
        }
        ]

        self.entry_rules = {"entryrules" : rules}

    def is_blocked_by_rules(self, url) -> bool:
        """
        Returns indication if URL is blocked by a rule
        """
        if not self.entry_rules:
            return False

        if "entryrules" not in self.entry_rules:
            return False

        for rule in self.entry_rules["entryrules"]:
            if self.is_url_hit(rule, url):
                return True

        return False

    def is_url_hit(self, rule, url) -> bool:
        """
        Returns indication if rule is applied to, connected with URL.
        """
        url_string = rule["rule_url"]

        rule_urls = self.get_rule_urls(url_string)

        for rule_url_pattern in rule_urls:
            if re.search(rule_url_pattern, url):
                return True

    def get_rule_urls(self, rule_url):
        """
        Returns URLs used by the rule
        """
        result = set()

        urls = rule_url.split(",")
        for url in urls:
            if url.strip() != "":
                result.add(url.strip())

        return result

    def get_browser(self, url) -> str | None:
        """
        Returns browser specified by rules for URL.
        Returns unique name of crawler_name
        """
        if not self.entry_rules:
            return

        if "entryrules" not in self.entry_rules:
            return

        for rule in self.entry_rules["entryrules"]:
            if self.is_url_hit(rule, url) and rule["browser"]:
                return rule["browser"]
