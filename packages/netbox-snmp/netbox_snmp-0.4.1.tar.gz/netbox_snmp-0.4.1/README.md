## Features
This plugin provide following Models:
* Trap Profiles
* User Profiles
* MIB Trees
* Notify Profiles

## Compatibility

|NetBox Version | Plugin    |
|---------------|-----------|
| NetBox 4.5.0  | >= 0.4.0  |

## Installation

The plugin is available as a Python package in pypi and can be installed with pip  

```
pip install netbox-snmp
```
Enable the plugin in /opt/netbox/netbox/netbox/configuration.py:
```
PLUGINS = ['netbox_snmp']
```
Restart NetBox and add `netbox-snmp` to your local_requirements.txt

See [NetBox Documentation](https://docs.netbox.dev/en/stable/plugins/#installing-plugins) for details

