# -*- coding: utf-8 -*-
"""
"""

import re
import time


HEX64 = re.compile("^[0-9a-f]{64}$")


class Filter:

    @property
    def events(self):
        return self.__dict__["#e"]

    @property
    def pubkeys(self):
        return self.__dict__["#p"]

    def __init__(self, cnf: dict = {}, **kw) -> None:
        self.ids = []
        self.authors = []
        self.kinds = []
        self.since = None
        self.until = None
        self.limit = 10
        self.__dict__["#e"] = []
        self.__dict__["#p"] = []

        self.load(cnf, **kw)

    def load(self, cnf: dict = {}, **kw) -> None:
        params = dict(cnf, **kw)
        if len(params):
            for key in [k for k in self.__dict__ if k in params]:
                value = params[key]
                if key == "#e":
                    key = "events"
                elif key == "#p":
                    key = "pubkeys"
                if key in ["since", "until", "limit"]:
                    setattr(self, key, value)
                else:
                    if isinstance(value, list):
                        getattr(self, key).extend(value)
                    else:
                        getattr(self, key).append(value)

    def apply(self):
        return dict([k, v] for k, v in self.__dict__.items() if v)

    def types(self, *ks):
        self.kinds.extend([k for k in ks if isinstance(k, int)])
        return self

    def since_now(self):
        self.since = int(time.time())
        return self

    def until_now(self):
        self.until = int(time.time())
        return self

    def published_by(self, *pubkeys):
        self.authors.extend([puk for puk in pubkeys if HEX64.match(puk)])
        return self

    def relative_to(self, *events):
        self.events.extend([evnt for evnt in events if HEX64.match(evnt)])
        return self

    def subcribe_to(self, *events):
        self.ids.extend([evnt for evnt in events if isinstance(evnt, str)])
        return self

    def mnimum_pow(self, difficulty: int):
        self.ids.extend(["0" * (difficulty // 4)])
        return self

    def count(self, limit=10):
        self.limit = limit
        return self
