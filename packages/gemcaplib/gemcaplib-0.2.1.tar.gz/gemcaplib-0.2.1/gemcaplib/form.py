!/usr/bin/env python

if __name__ == '__main__':
    print("31 /\r\n")
    exit()

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Dict, Optional

from .database import EntryIdentifier
from .database import db as database
from .gemini import request_data
from .ui import quote


class FormItemType(IntEnum):
    TEXT = 0
    LINK = 1
    CHECK = 2
    RADIO = 3
    MULTI = 4

@dataclass
class FormItem:
    def __hash__(self):
        return hash(self.name)

    name: str
    type: FormItemType
    required: bool = False
    require_identity: bool = False # Require an identity to render
    onEditCallback: Callable | None = None # Do something when this input changes specifically

    title: Optional[str] = None
    subtitle: Optional[str] = None
    display: Optional[str] = None
    input_text: str = ""

    value: Optional[Any] = None
    options: Optional[list] = field(default_factory=list)

def text_input(name, display, input_text="", required=False, title=None, value=None, subtitle=None, require_identity=False, onEditCallback=None):
    return FormItem(
        name=name,
        type=FormItemType.TEXT,
        required=required,
        title=title,
        subtitle=subtitle,
        display=display,
        value=value,
        input_text=input_text,
        require_identity=require_identity,
        onEditCallback=onEditCallback,
    )


def link_input(name, display, input_text="", required=False, title=None, value=None, subtitle=None, require_identity=False, onEditCallback=None):
    return FormItem(
        name=name,
        type=FormItemType.LINK,
        required=required,
        title=title,
        subtitle=subtitle,
        display=display,
        value=value,
        input_text=input_text,
        require_identity=require_identity,
        onEditCallback=onEditCallback,
    )


def check_input(name, display, required=False, title=None, default=False, subtitle=None, require_identity=False, onEditCallback=None):
    return FormItem(
        name=name,
        type=FormItemType.CHECK,
        required=required,
        title=title,
        subtitle=subtitle,
        display=display,
        value=default,
        require_identity=require_identity,
        onEditCallback=onEditCallback,
    )


def radio_input(name, options, required=False, title=None, default=False, subtitle=None, require_identity=False, onEditCallback=None):
    return FormItem(
        name=name,
        type=FormItemType.RADIO,
        required=required,
        title=title,
        subtitle=subtitle,
        options=options,
        value=default,
        require_identity=require_identity,
        onEditCallback=onEditCallback,
    )


def multi_input(name, options, required=False, title=None, subtitle=None, require_identity=False, onEditCallback=None):
    v = {}
    for i, _ in enumerate(options):
        v[i] = False
    return FormItem(
        name=name,
        type=FormItemType.MULTI,
        required=required,
        title=title,
        subtitle=subtitle,
        options=options,
        value=v,
        require_identity=require_identity,
        onEditCallback=onEditCallback,
    )


@dataclass
class Form:
    id: EntryIdentifier
    body: Dict[str, FormItem] = field(default_factory=Dict)
    require_identity: bool = False # Require an identity to view this entire form

    current_input: Optional[str] = None
    completed: bool = False
    onRenderCallback: Callable | None = None

    def render(self):
        if self.onRenderCallback:
            self.onRenderCallback(self)
        # Skip entire form if it requires an identity and we don't have one.
        if self.require_identity and request_data.client_tls_hash == "":
            return
        entry = database.get(self.id.query())
        body = None
        if entry:
            body = entry.get("body")
        if body is None:
            return
        for id, item in body.items():
            if item.get("require_identity"): #If not set at all, returns None, if false then false, so win win
                if request_data.client_tls_hash == "":
                    continue
            type = item.get("type")
            base_link = f"{request_data.gemini_url.split("?")[0]}?{item.get("name")}"
            display = f"{item.get("display") if item.get("display") else item.get("name")}"

            if item.get("title"):
                print(f"## {item.get('title')}")
            if item.get("subtitle"):
                print(item.get("subtitle"))

            if type == FormItemType.TEXT:
                print(f"=> {base_link} ✍️ {display}")
                if item.get("value"):
                    quote(item.get("value"))

            elif type == FormItemType.LINK:
                print(f"=> {base_link} ⛓️ {display}")
                if item.get("value"):
                    quote(item.get("value"))

            elif type == FormItemType.CHECK:
                print(f"=> {base_link} {'⬜️' if not bool(item.get("value")) else '✅'} {display}")

            elif type == FormItemType.RADIO:
                for i, option in enumerate(item.get("options")):
                    print(f"=> {base_link}:{i} {'⭕' if i != int(item.get("value")) else '🔘'} {option}")

            elif type == FormItemType.MULTI:
                for i, option in enumerate(item.get("options")):
                    value = item.get("value")
                    print(f"=> {base_link}:{i} {'⬜️' if not value.get(str(i)) else '✅'} {option}")
            print()

    def _to_database_entry(self):
        body = dict()
        for id, item in self.body.items():
            body[id] = dict()
            body[id]["name"] = item.name
            body[id]["type"] = item.type
            body[id]["required"] = item.required
            body[id]["title"] = item.title
            body[id]["subtitle"] = item.subtitle
            body[id]["display"] = item.display
            body[id]["input_text"] = item.input_text
            body[id]["value"] = item.value
            body[id]["options"] = item.options
            body[id]["require_identity"] = item.require_identity

        db_entry = {
            "group": self.id.group,
            "name": self.id.name,
            "client": self.id.client,
            "current_input": self.current_input,
            "completed": self.completed,
            "require_identity": self.require_identity,
            "body": body
        }

        return db_entry

    def load(self):
        entry = database.get(self.id.query())
        if not entry:
            database.insert(self._to_database_entry())
            entry = database.get(self.id.query())

        self.id.group = entry.get("group")
        self.id.name = entry.get("name")
        self.id.client = entry.get("client")

        self.current_input = entry.get("current_input")
        self.completed = entry.get("completed")

        body = entry.get("body")
        for id, item in body.items():
            self.body[id] = FormItem(
                name = item.get("name"),
                type = item.get("type"),
                required = item.get("required"),
                title = item.get("title"),
                subtitle = item.get("subtitle"),
                display = item.get("display"),
                input_text = item.get("input_text"),
                value = item.get("value"),
                options = item.get("options"),
                require_identity= item.get("require_identity"),
                onEditCallback=self.body[id].onEditCallback
            )

    def _serialize_body(self):
        serialized = dict()
        for id, item in self.body.items():
            serialized[id] = dict()
            serialized[id]["name"] = item.name
            serialized[id]["type"] = item.type
            serialized[id]["required"] = item.required
            serialized[id]["title"] = item.title
            serialized[id]["subtitle"] = item.subtitle
            serialized[id]["display"] = item.display
            serialized[id]["input_text"] = item.input_text
            serialized[id]["require_identity"] = item.require_identity
            serialized[id]["value"] = item.value
            serialized[id]["options"] = item.options
        return serialized

    def save(self):
        entry = database.get(self.id.query())
        if entry:
            # Update the existing entry with new values
            update_data = {
                "body": self._serialize_body(),
                "current_input": self.current_input,
                "completed": self.completed
            }
            database.update(update_data, self.id.query())
