#!/usr/bin/env python3

import argparse
import socket
import struct
import validators

INITIALIZATION_VECTOR = 171
RESPONSE_LENGTH = 4096

def autokey(plaintext):
    key = INITIALIZATION_VECTOR
    result = bytes()
    for byte in plaintext:
        xor = key ^ byte
        key = xor
        result += bytes([xor])
    return result

def decrypt(encrypted):
    key = INITIALIZATION_VECTOR
    result = ""
    for byte in encrypted:
        xor = key ^ byte
        key = byte
        result += chr(xor)
    return result

parser = argparse.ArgumentParser(description='connect to TP-Link smart plug HS105')
parser.add_argument("-i", "--host_ip",
                    help="Target hostname or IP address")
parser.add_argument('--port', type=int, default=9999,
                    help='the port of the smart plug to connect to')
parser.add_argument('--command_cat', type=str,
                    help='what category of command (cloud, netif, schedule, system, time)')
parser.add_argument('--command', type=str,
                    help='what command (Cloud: unbind, <enter valid server URL>. \
                                        Netif: scan_networks, get_wifi_info. \
                                        Schedule: delete_all_rules, get_rules. \
                                        System: info, on, off. \
                                        Time: time)')
arg = parser.parse_args()


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # don't need to wait for request to timeout
target = socket.gethostbyname(arg.host_ip)
port=arg.port
s.connect((target, port)) # tuple

com_cat = arg.command_cat
command=arg.command
command_dict = ""

if com_cat == "cloud":
    if command == "unbind":
        command_dict = '{"cnCloud":{"unbind":null}}'
    elif validators.url(command): # valid url
        command_dict = '{"cnCloud":{"set_server_url":{"server":"%s"}}}' % command
elif com_cat == "netif":
    if command == "scan_networks":
        command_dict = '{"netif":{"get_scaninfo":{"refresh":1}}}'
    elif command == "get_wifi_info":
        command_dict = '{"netif":{"get_stainfo":{}}}'
elif com_cat == 'schedule':
    if command == "delete_all_rules":
        command_dict = '{"schedule":{"delete_all_rules":null,"erase_runtime_stat":null}}'
    elif command == "get_rules":
        command_dict = '{"schedule":{"get_rules":null}}'
elif com_cat == 'system':
    if command == "on" or command == "off":
        command_dict = '{"system":{"set_relay_state":{"state":%i}}}' % (command == "on")
    elif command == "info":
        command_dict = '{"system":{"get_sysinfo":null}}'
elif command == 'time':
    command_dict = '{"time":{"get_time":{}}}'
else:
    raise Exception("you entered the command wrong somehow...")

encrypted_command = struct.pack(">I", len(command_dict)) + autokey(command_dict.encode())
s.send(encrypted_command)

response = s.recv(RESPONSE_LENGTH)
decrypted_response = decrypt(response)

if "\"err_code\":0" in decrypted_response:
    print(decrypted_response)
    print(f"success! you just changed the {com_cat}")
else:
    print("oops, try again")

s.close()
