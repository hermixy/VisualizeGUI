# VisualizeGUI

## Build Executable
Built executable file can be found in the dist/ folder
```
python create_executable.py -f <filename.py>
```

## ZMQ Motor GUI
Controls rotational controller. Run servers in background:
```
python server1.py COM#
```

## Server List
Position (PUB/SUB)
```
pubsub_server1.py 6011 10000
pubsub_server2.py 6013 11000
```

Parameters (PUB/SUB)
```
pubsub_server1.py 6010 
pubsub_server2.py 6012
```

Plot (REQUEST/REPLY)
```
reqrep_server1.py 6002 10001
reqrep_server2.py 6009 10009
```

Motor Control (Position, PUB/SUB)
```
server1.py 6011 10000
server2.py 6013 10000
```

Motor Control (Parameter, REQ/REP)
```
server1.py 6010 10000
server2.py 6012 10000
```


