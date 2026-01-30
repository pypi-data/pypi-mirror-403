#!/usr/bin/env python

if __name__ == '__main__':
    print("31 /\r\n")
    exit()

from dataclasses import dataclass, field
from typing import List


@dataclass
class Locale:
    submit_page: str = "🪐 Submit page"
    reset_page: str = "🔄 Reset this page"
    footer_message: str = ""

@dataclass
class ServerAdapter:
    separate_query: bool = True # my server includes the query in gemini_url always, it'd be nice to just keep them separate TODO what... does this mean exactly...?

    gemini_url: str = "GEMINI_URL"
    identity_hash: str = "TLS_CLIENT_HASH"
    identity_name: str = "REMOTE_USER"
    query_string: str = "QUERY_STRING"

@dataclass
class Config:
    database_name: str = "gcl"
    lang: str = "en"
    charset: str = "utf-8"
    locale: Locale = field(default_factory=Locale)

    character_blacklist: List[str] = field(default_factory=lambda: ["`"])

    server_adapter: ServerAdapter = field(default_factory=ServerAdapter)

    debugging: bool = False #Completely breaks Gemtext compliance, made for console debugging.

data = Config()
