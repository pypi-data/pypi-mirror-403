#!/usr/bin/env python3
import os
import re

def validate():
    if not os.path.exists("main.tf"):
        message = "main.tf is missing."
        return False, message

    with open("main.tf") as f:
        content = f.read()

    if not re.search(r'provider\s+"aws"\s*\{', content):
        message = 'Provider "aws" block is missing.'
        return False, message

    if not re.search(r'region\s*=\s*"us-east-1"', content):
        message = 'Provider aws must define region = "us-east-1".'
        return False, message

    message = "Terraform provider block is correct!"
    return True, message

if __name__ == "__main__":
    ok, message = validate()
    print(message)
