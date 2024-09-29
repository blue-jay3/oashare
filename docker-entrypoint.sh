#!/bin/sh
python p2p-server.py &
sleep 1
python p2p-client.py
