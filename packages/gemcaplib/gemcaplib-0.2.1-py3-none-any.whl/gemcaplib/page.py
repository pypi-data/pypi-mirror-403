#!/usr/bin/env python

if __name__ == '__main__':
    print("31 /\r\n")
    exit()

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Callable, Dict

from .config import data as config
from .form import Form, FormItemType
from .gemini import (
    client_input,
    page_error_identity,
    page_error_request,
    page_error_server,
    page_headers,
    page_redirect,
    request_data,
)

# TODO move this to a config variable list we "|".join on
def valid_link(link):
    from re import match
    if match(r"^(http(s?)|gemini|gopher|finger):([/|.|\w|\s|-])*\.*$", link):
        return True
    return False


def valid_text(text: str) -> bool:
    if text is None:
        return False
    for char in config.character_blacklist:
        if char in text:
            return False
    return True


def error_handler(error: "Error"):
    # Assume server
    handler_callback = page_error_server
    if error.type == ErrorType.REQUEST:
        handler_callback = page_error_request
    elif error.type == ErrorType.IDENTITY:
        handler_callback = page_error_identity
    handler_callback(str(error.message))


def process_form(page: "Page", form_id):
    if(request_data.client_tls_hash is None): # TODO this doesn't work, but also... anonymous forms with shared input can have their use and I've been writing anon forms from the start lol
        page.errors.append(Error(ErrorType.IDENTITY, "An identity is required to use forms."))
        return

    page.forms[form_id].load() # sync from DB
    page.debug(f"- Processing Form \"{page.forms[form_id].id}\"")

    # Do we have a change with a second step current requested? Process it and redirect!
    if page.forms[form_id].current_input is not None:
        key = page.forms[form_id].current_input
        for id, item in page.forms[form_id].body.items():
            if item.name == key:
                page.debug(f"-- Processing \"{item.name}\"")
                #validation time
                if item.type == FormItemType.TEXT:
                    if not valid_text(str(request_data.query_string)):
                        page.debug("--- Invalid text input")
                        page.errors.append(Error(ErrorType.REQUEST, "Blacklisted characters have been used."))
                        page.forms[form_id].current_input = None
                        page.forms[form_id].save()
                        return

                elif item.type == FormItemType.LINK:
                    if not valid_link(str(request_data.query_string)):
                        page.debug("--- Invalid link input")
                        page.errors.append(Error(ErrorType.REQUEST, "Invalid link provided. Supported protocols: gemini, gopher, finger, http/s. PLEASE REFRESH THE PAGE."))
                        page.forms[form_id].current_input = None
                        page.forms[form_id].save()
                        return

                page.forms[form_id].body[id].value = request_data.query_string
                page.forms[form_id].current_input = None
                if item.onEditCallback:
                    page.debug("--- Running onEditCallback")
                    item.onEditCallback(page, request_data.query_string)
                break # We can only ever process one input so...


        page.forms[form_id].save()
        page_redirect(request_data.gemini_url)

    # do we have a query? Initiates a new form change, OR processes one step changes! 
    query = request_data.query_string
    subarg = ""
    if query:
        if len(query.split(":")) > 1: # Kind of an unofficial splitting character, but moreso used for unique IDs in form subitems (multi select, radio). Not dynamic input
            query, subarg = query.split(":")
    body = page.forms[form_id].body
    for id, item in body.items():
        if item.name == query and query is not None:
            page.debug(f"-- Setting up {item.name}")

            if item.require_identity and request_data.client_tls_hash == "":
                page.debug("--- Unauthorized input request")
                page.errors.append(Error(ErrorType.IDENTITY, "An identity is required to access this resource."))
                page.forms[form_id].current_input = None
                page.forms[form_id].save()
                return

            page.forms[form_id].current_input = query
            page.forms[form_id].save()
            if item.type in [FormItemType.TEXT, FormItemType.LINK]:
                client_input(message=item.input_text)

            if item.type == FormItemType.CHECK:
                page.forms[form_id].body[id].value = not bool(item.value)
                page.forms[form_id].current_input = None
                page.forms[form_id].save()
                page_redirect(request_data.gemini_url)

            if item.type == FormItemType.RADIO:
                if int(subarg) < len(item.options):
                    page.forms[form_id].body[id].value = int(subarg)
                    page.forms[form_id].current_input = None
                    page.forms[form_id].save()
                    page_redirect(request_data.gemini_url)

            if item.type == FormItemType.MULTI:
                if int(subarg) < len(item.options):
                    page.forms[form_id].body[id].value[subarg] = not page.forms[form_id].body[id].value[subarg]
                    page.forms[form_id].current_input = None
                    page.forms[form_id].save()
                    page_redirect(request_data.gemini_url)

    page.forms[form_id].completed = True
    for id, item in body.items():
        if item.value is None and item.required:
            page.forms[form_id].completed = False

    page.forms[form_id].save()


class ErrorType(IntEnum):
    REQUEST = 0,
    SERVER = 1,
    IDENTITY = 2,

@dataclass
class Error:
    type: ErrorType
    message: str | None


@dataclass
class Page:
    require_identity: bool = False
    forms: Dict[str, Form] = field(default_factory=dict)
    errors: list = field(default_factory=list)
    submitCallback: Callable | None = None
    onLoadCallback: Callable | None = None

    error_handler: Callable = error_handler

    def start(self):
        self.debug(f"Rendering page \"{request_data.gemini_url}\"")
        if self.require_identity:
            page_error_identity()

        if self.onLoadCallback:
            self.debug("- Running onLoadCallback")
            self.onLoadCallback(self)

        if request_data.query_string == "resetPage":
            self.debug("- Page reset")
            self.reset()
            page_redirect(request_data.gemini_url)
        if request_data.query_string == "submitPage":
            self.debug("- Page submit")
            completed = True
            for id, form in self.forms.items():
                form.load()
                if not form.completed:
                    self.debug("- Submit fail!")
                    completed = False
            if self.submitCallback and completed:
                self.debug("- Submit success")
                self.submitCallback(self)

            # If we get here, the callback didn't supply an exit.
            page_redirect(request_data.gemini_url)

        if self.forms is not None:
            for form_id, _ in self.forms.items():
                process_form(self, form_id)

        if len(self.errors):
            self.error_handler(self.errors[0])

        page_headers()


    def submitter(self):
        completed = True
        for id, form in self.forms.items():
            if not form.completed:
                completed = False
        if self.submitCallback and completed:
            print(f"\n=> {request_data.gemini_url}?submitPage {config.locale.submit_page}\n")


    def footer(self):
        if len(self.forms) > 0:
            print(f"\n=> {request_data.gemini_url}?resetPage {config.locale.reset_page}\n")
        print(config.locale.footer_message, end="\n" if config.locale.footer_message != "" else "")

    # Saving the form before a DB sync (load) means that the original non-filled out form is in memory. This sends the update to save a user's form as the original definition of the form (empty). 
    # REALLY IMPORTANTLY AND USEFULLY BY THE WAY IS THAT RESETTING THE FORM WILL UPDATE IT TO THE NEWEST VERSION IF YOUVE BEEN WORKING ON A FORM.
    def reset(self):
        for id, form in self.forms.items():
            form.save()

    # Debug printing, if Debug is enabled then print
    def debug(self, message):
        if(config.debugging):
            print(message)
