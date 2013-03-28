openmm-builder
==============

A graphical interface for building OpenMM scripts. As you edit the fields in the GUI, the script will
update itself in real time.

![image](https://raw.github.com/rmcgibbo/openmm-builder/master/screenshot.png)

Installation
------------
openmm-builder depends on enthought's [traits](https://pypi.python.org/pypi/traits) and
[traitsui](https://pypi.python.org/pypi/traitsui) on top of the Qt graphics toolkit.
I am also, for simplicity, using [mustache](http://mustache.github.com/) to generate the script.

To install this stuff with `easy_install`, just do:

```
$ sudo easy_install traits traitsui pystache
```
  
