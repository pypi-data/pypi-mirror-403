#!/usr/bin/env python3
import os
import re

def read(path):
    with open(path) as f:
        return f.read()

def validate():
    required_files = ["variables.tf", "main.tf", "outputs.tf"]

    for file in required_files:
        if not os.path.exists(file):
            message = f"{file} missing."
            return False, message

    vars_tf = read("variables.tf")
    main_tf = read("main.tf")
    out_tf  = read("outputs.tf")

    # --- Variables ---
    if not re.search(r'variable\s+"instance_type"\s*\{', vars_tf):
        message = 'variable "instance_type" missing.'
        return False, message

    if not re.search(r'variable\s+"ami"\s*\{', vars_tf):
        message = 'variable "ami" missing.'
        return False, message

    # --- Resource ---
    if not re.search(r'resource\s+"aws_instance"\s+"dev"\s*\{', main_tf):
        message = 'Resource "aws_instance" "dev" missing.'
        return False, message

    if not re.search(r'instance_type\s*=\s*var\.instance_type', main_tf):
        message = "instance_type must reference var.instance_type."
        return False, message

    if not re.search(r'ami\s*=\s*var\.ami', main_tf):
        message = "ami must reference var.ami."
        return False, message

    # Ensure no hardcoding
    if re.search(r'instance_type\s*=\s*"', main_tf):
        message = "instance_type must not be hardcoded."
        return False, message

    if re.search(r'ami\s*=\s*"', main_tf):
        message = "ami must not be hardcoded."
        return False, message

    # --- Output ---
    if not re.search(r'output\s+"instance_id"\s*\{', out_tf):
        message = 'Output "instance_id" missing.'
        return False, message

    if not re.search(r'value\s*=\s*aws_instance\.dev\.id', out_tf):
        message = "Output instance_id must reference aws_instance.dev.id."
        return False, message

    message = "Hard Terraform lab validated successfully!"
    return True, message


if __name__ == "__main__":
    ok, message = validate()
    print(message)
