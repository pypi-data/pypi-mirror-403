#!/usr/bin/env python

if __name__ == '__main__':
    print("31 /\r\n")
    exit()

# Eh I just find myself using these a lot making UIs

def page_spacer():
    print("\n\n")

def page_spacer_small():
    print("\n")

def quote(text: str):
    for line in text.split("\n"):
        print(f"> {line}")
