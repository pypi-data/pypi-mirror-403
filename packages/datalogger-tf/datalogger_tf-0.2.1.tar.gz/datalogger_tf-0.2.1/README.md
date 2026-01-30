# datalogger-gui

A GUI interfaced software to log multiple instruments via ethernet, usb or serial connection.

`./datalogger-gui`

![screenshot](doc/datalogger-gui.png)

## Usage

- Select the instrument to log
- Check the IP/serial/usb address
- enter a sample time (default = 1)
- select a channel
- precise the type
- press start

## Saving Tree

Each daily file is saved in a tree as following:
```
~/server/data/
└── YYYY
    └── YYYY-MM
        └── YYYYMMDD-hhmmss-instrument.dat
```

* You can override the base directory (i.e. '~/server/data/') using command line argument '-od' (or '--output-directory').

* You can disable creation of tree using command line argumenr '-ddc' (or '--disable-directory-creation').
