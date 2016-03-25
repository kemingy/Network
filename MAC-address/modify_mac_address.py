# -*- coding: utf-8 -*-
# modify MAC address
# run this with administrative privileges if you want to change your MAC address
# !!! This works under Chinese !!!

# import os
# import sys
# import ctypes
import re
# import random
# import platform
import _winreg as winreg
import subprocess

# regex to MAC address like 00-00-00-00-00-00 or 00:00:00:00:00:00 or
# 000000000000
MAC_ADDRESS_RE = re.compile(r"""
    ([0-9A-F]{1,2})[:-]?
    ([0-9A-F]{1,2})[:-]?
    ([0-9A-F]{1,2})[:-]?
    ([0-9A-F]{1,2})[:-]?
    ([0-9A-F]{1,2})[:-]?
    ([0-9A-F]{1,2})
    """,
    re.I | re.VERBOSE
) # re.I: case-insensitive matching. re.VERBOSE: just look nicer.

WIN_REGISTRY_PATH = "SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}"

mac_info = subprocess.check_output('GETMAC /v /FO list', stderr=subprocess.STDOUT)
print 'Your MAC address:\n'
print mac_info

# is user an admin?
if ctypes.windll.shell32.IsUserAnAdmin() == 0:
    print 'Sorry! You should run this with administrative privileges if you want to change your MAC address.'
    sys.exit()

# get the dict[link name : MAC address]
link_name = re.findall(r'\r\n\xc1\xac\xbd\xd3\xc3\xfb:\s+(.+?)\r\n\xcd\xf8\xc2\xe7\xca\xca\xc5\xe4\xc6\xf7', mac_info)
mac_address = re.findall(r'\r\n\xce\xef\xc0\xed\xb5\xd8\xd6\xb7:\s+(.+?)\r\n\xb4\xab\xca\xe4\xc3\xfb\xb3\xc6', mac_info)
name_mac = zip(link_name, mac_address)
name_mac_dict = dict(name_mac)

def get_mac_address():
    """
    get the new MAC address and normalize it
    """
    mac_address = raw_input('Please input your new MAC address: ')
    while not MAC_ADDRESS_RE.match(mac_address):
        mac_address = raw_input('Wrong input! Please input a correct MAC address: ')

    # normalize the MAC address
    return '-'.join([g.zfill(2) for g in MAC_ADDRESS_RE.match(mac_address).groups()]).upper()

def get_device():
    """
    get the device
    """
    print '==========================================================='
    for name in link_name:
        print name, ' | ',

    print
    input_name = raw_input('Please input the link name above you want to change: ')
    while input_name not in link_name:
        input_name = raw_input('Wrong input! Please input again: ')

    return input_name

def restart_adapter(self, device):
    """
    Disables and then re-enables device interface
    """
    if platform.release() == 'XP':
        description, adapter_name, address, current_address = find_interface(device)
        cmd = "devcon hwids =net"
        try:
            result = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except FileNotFoundError:
            raise
        query = '('+description+'\r\n\s*.*:\r\n\s*)PCI\\\\(([A-Z]|[0-9]|_|&)*)'
        query = query.encode('ascii')
        match = re.search(query,result)
        cmd = 'devcon restart "PCI\\' + str(match.group(2).decode('ascii'))+ '"'
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)

    else:
        cmd = "netsh interface set interface \"" + device + "\" disable"
        subprocess.check_output(cmd)
        cmd = "netsh interface set interface \"" + device + "\" enable"
        subprocess.check_output(cmd)

def set_mac_address():
    """

    """
    # Locate adapter's registry and update network address (mac)
    reg_hdl = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    key = winreg.OpenKey(reg_hdl, WIN_REGISTRY_PATH)
    info = winreg.QueryInfoKey(key)

    # Find adapter key based on sub keys
    adapter_key = None
    adapter_path = None

    for x in range(info[0]):
        subkey = winreg.EnumKey(key, x)
        path = self.WIN_REGISTRY_PATH + "\\" + subkey

        if subkey == 'Properties':
            break

        # Check for adapter match for appropriate interface
        new_key = winreg.OpenKey(reg_hdl, path)
        try:
            adapterDesc = winreg.QueryValueEx(new_key, "DriverDesc")
            if adapterDesc[0] == target_device:
                adapter_path = path
                break
            else:
                winreg.CloseKey(new_key)
        except (WindowsError) as err:
            if err.errno == 2:  # register value not found, ok to ignore
                pass
            else:
                raise err

    if adapter_path is None:
        winreg.CloseKey(key)
        winreg.CloseKey(reg_hdl)
        return

    # Registry path found update mac addr
    adapter_key = winreg.OpenKey(reg_hdl, adapter_path, 0, winreg.KEY_WRITE)
    winreg.SetValueEx(adapter_key, "NetworkAddress", 0, winreg.REG_SZ, new_mac)
    winreg.CloseKey(adapter_key)
    winreg.CloseKey(key)
    winreg.CloseKey(reg_hdl)

    # Adapter must be restarted in order for change to take affect
    restart_adapter(adapter_name)

target_device = get_device()
print 'Your target device is: ' + target_device
new_mac = get_mac_address()
set_mac_address()
print 'Your new mac is: ' + new_mac
