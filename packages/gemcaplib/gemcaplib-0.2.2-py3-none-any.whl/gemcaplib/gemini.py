#!/usr/bin/env python

if __name__ == '__main__':
    print("31 /\r\n")
    exit()

import os
from .config import data as config

class RequestData:
    def __init__(self, gemini_url, client_tls_hash, client_name, query_string):
        self.gemini_url: str = gemini_url
        self.client_tls_hash: str = client_tls_hash
        self.client_name: str = client_name
        self.query_string = query_string

adapter = config.server_adapter

request_data = RequestData(
    gemini_url=os.environ.get(adapter.gemini_url, ""),
    client_tls_hash=os.environ.get(adapter.identity_hash, ""), # TODO allow this to be None, but update that one instance that is supposed to block anon forms to not do that
    client_name=os.environ.get(adapter.identity_name),
    query_string=os.environ.get(adapter.query_string)
)

if adapter.separate_query:
    request_data.gemini_url = request_data.gemini_url.split("?")[0]

def page_headers(charset=config.charset, lang=config.lang):
    print(f"20 text/gemini; charset={charset};lang={lang};\r\n")

def client_input(message: str):
    print(f"10 {message}\r\n")
    exit()

def page_redirect(where: str):
    print(f"31 {where}\r\n")
    exit()

def page_error_server(message = ""):
    print(f"42 {message}\r\n")
    exit()

def page_error_request(message = ""):
    print(f"50 {message}\r\n")
    exit()

def page_error_identity(message = "Identity required to view this page."):
    print(f"60 {message}\r\n")
    exit()
