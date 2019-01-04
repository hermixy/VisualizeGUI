# VisualizeGUI

## Build Executable
Built executable file can be found in the dist/ folder
```
python create_executable.py -f <filename.py>
```

## ZMQ Motor GUI
![](/doc/example.gif)

Controls rotational controller. Run servers in background:
```
python server1.py COM#
python reqrep_server1.py
python reqrep_server2.py
pubsub_server2.py
```

## Server List
Symbols at end denote combinations

Position (PUB/SUB)
```
pubsub_server1.py 6011 10000 *
pubsub_server2.py 6013 11000 *  <- Use if server1.py running
```

Parameters (PUB/SUB)
```
pubsub_server1.py 6010  =
pubsub_server2.py 6012 = ^
```

Plot (REQUEST/REPLY)
```
reqrep_server1.py 6002 10001 -
reqrep_server2.py 6009 10009 -
```

Motor Control (Position, PUB/SUB)
```
server1.py 6011 10000 *
server2.py 6013 10000
```

Motor Control (Parameter, REQ/REP)
```
server1.py 6010 10000 ^
server2.py 6012 10000
```

Switch pubsub_server1.py for server1.py (One at a time)

