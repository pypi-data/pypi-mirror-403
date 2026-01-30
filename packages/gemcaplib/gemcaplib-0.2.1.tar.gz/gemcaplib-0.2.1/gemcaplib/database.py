#!/usr/bin/env python

if __name__ == '__main__':
    print("31 /\r\n")
    exit()

import os
from dataclasses import dataclass

from tinydb import Query, TinyDB

from .config import data as config
from .gemini import request_data

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))

db = TinyDB(f"{os.path.join(current_dir, config.database_name)}.db")

@dataclass
class EntryIdentifier:
    group: str #Used to specify arbitrary things like "system" or "account". Then subforms can be within those.
    name: str
    client: str = request_data.client_tls_hash

    def __str__(self):
        return f"Group: {self.group}, Name: {self.name}, Client: {self.client}"

    def query(self):
        return (
            (Query().group == self.group) &
            (Query().name == self.name) &
            (Query().client == self.client)
        )
