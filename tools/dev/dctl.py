"""Send one JSON command to dserve.py and print the reply: dctl.py '{"op":"shot","path":"x.png"}'"""
import json
import socket
import sys

port = 5599
s = socket.create_connection(('127.0.0.1', port), timeout=900)
s.sendall((sys.argv[1] + '\n').encode())
print(s.makefile().readline().strip())
