# ac-pserver

ac-pserver is a Python 3 rewrite of the example C# UDP server, written by Kunos for [Assetto Corsa](http://www.assettocorsa.net/en/).

It is just meant as a starting point: by default it simply prints on the command line the information sent by the server, and provides send/receive method through a Pserver class. The code should be pretty self explanatory.

Make sure that UDP_IP, UDP_PORT, and UDP_SEND_PORT match the values of UDP_PLUGIN_ADDRESS and UDP_PLUGIN_LOCAL_PORT of yourserver_cfg.ini respectively.

To run:

`python3 pserver.py`

In production you would probably want to use a process control system such as [Supervisor](http://supervisord.org/).

