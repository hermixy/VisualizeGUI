## Rotational Controller GUI
Controls rotational controller with precise movement velocity, acceleration, and positional accuracy. 

<p float="left">
    <img src="/doc/rotational_controller_single_dark_hd.gif" width='900'/>
</p>

Controls rotational controller. Run servers in background:
```
python rotational_controller_server.py <COM#>
```

#### Rotational Controller Server Settings

Motor Control (Position, PUB/SUB)
```
Port: 6011
Topic: 10000
```

Motor Control (Parameter, REQ/REP)
```
Port: 6010
Topic: 10000
```

Example rotational.ini configuration file
```
[ROTATIONAL_CONTROLLER]
position_frequency = .025
position_address = tcp://192.168.1.143:6011
parameter_address = tcp://192.168.1.143:6010
position_topic = 10000
```

## Universal Plot GUI

![](/doc/universal_plot_dark.gif)

## GUI Widget Examples
Look in /examples for individual GUI module components

## Build Executable
Built executable file can be found in the dist/ folder
```
python create_executable.py -f <GUI_filename.py>
```
Executable will be in the created dist/ folder

