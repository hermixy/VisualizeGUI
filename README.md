# VisualizeGUI

## Build Executable
Built executable file can be found in the dist/ folder
```
python create_executable.py -f <filename.py>
```
Executable will be in the created dist/ folder

## Rotational Controller GUI
Controls rotational controller with precise movement velocity, acceleration, and positional accuracy. 

![light](/doc/rotational_controller.gif) ![dark](/doc/rotational_controller_dark.gif)

Controls rotational controller. Run servers in background:
```
python rotational_controller_server.py COM#
python rotational_plot_server.py
python rotational_plot_server_alt.py
python rotational_parameter_position_server.py
```

rotational_controller_server is required. All others are optional.

## Server List
Symbols at end denote combinations

Position (PUB/SUB)
```
rotational_parameter_position_server.py 6013 11000 *  <- Use if rotational_controller_server.py running
rotational_parameter_position_server_alt.py 6011 10000 *
```

Parameters (PUB/SUB)
```
rotational_parameter_position_server.py 6012 = ^
rotational_parameter_position_server_alt.py 6010  =
```

Plot (REQUEST/REPLY)
```
rotational_plot_server.py 6002 10001 -
rotational_plot_server_alt.py 6009 10009 -
```

Motor Control (Position, PUB/SUB)
```
rotational_controller_server.py 6011 10000 *
rotational_controller_server_alt.py 6013 10000
```

Motor Control (Parameter, REQ/REP)
```
rotational_controller_server.py 6010 10000 ^
rotational_controller_server_alt.py 6012 10000
```

Switch rotational_parameter_position_server_alt.py for rotational_controller_server.py (One at a time)

