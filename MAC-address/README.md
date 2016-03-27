# 中文版Windows下利用Python修改MAC地址 #

-------------------------

## 说明 ##

* 此时用的系统为Windows10，理论上适用于Windows XP/7/8/8.1/10，如发现问题，请联系我
* Python版本为2.7
* 源码参考自feross的SpoofMAC：https://github.com/feross/SpoofMAC.git
* 关于MAC地址全球唯一的问题，这里修改的仅是ARP缓存表中的地址，如果你利用 `ipconfig /all` 查看的是网卡中的MAC地址，而要修改这个网卡中的地址的话只能用厂家提供的修改程序。[参考：http://blog.chinaunix.net/uid-30329684-id-5111976.html]
* 当然修改MAC地址的方法很多，可以手动打开网卡的配置进行修改，具体方法很容易从网上获取


-------------------------

## 详解 ##

### 验证用户权限 ###
``` python
import ctypes
if ctypes.windll.shell32.IsUserAnAdmin() == 0:
    print 'Sorry! You should run this with administrative privileges if you want to change your MAC address.'
    sys.exit()
```

### 获取MAC详细信息 ###
这里用的是 `getmac /v /FO list`
``` python
import subprocess
mac_info = subprocess.check_output('GETMAC /v /FO list', stderr=subprocess.STDOUT)
print 'Your MAC address:\n'
print mac_info
```

### 提取信息 ###
得到的信息有连接名、网络适配器、物理地址（MAC）和传输名称，其中网络适配器之后会用于匹配注册表，所以这里需要提取出网络适配器和物理地址。

由于系统是中文的，在编码方面会有些问题，所以直接在正则表达式中使用默认的编码了。
``` python
network_adapter = re.findall(r'\r\n\xcd\xf8\xc2\xe7\xca\xca\xc5\xe4\xc6\xf7:\s+(.+?)\r\n\xce\xef\xc0\xed\xb5\xd8\xd6\xb7', mac_info)
mac_address = re.findall(r'\r\n\xce\xef\xc0\xed\xb5\xd8\xd6\xb7:\s+(.+?)\r\n\xb4\xab\xca\xe4\xc3\xfb\xb3\xc6', mac_info)
```

### 匹配MAC地址 ###
Windows下常见的MAC格式有：00-00-00-00-00-00 或者 00:00:00:00:00:00 或者 000000000000
``` python
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
```
获取之后进行格式化
```python
return '-'.join([g.zfill(2) for g in MAC_ADDRESS_RE.match(mac_address).groups()]).upper()
```
这里的匹配并没有检查是否有多余输入，即使输入1000个0，也只会匹配前12个

### 设置MAC地址 ###
首先要从注册表中获取相关信息
```python
WIN_REGISTRY_PATH = "SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}"
reg_hdl = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
key = winreg.OpenKey(reg_hdl, WIN_REGISTRY_PATH)
info = winreg.QueryInfoKey(key)
```
之后，寻找需要更改的设备路径
```python
for index in range(info[0]):
    subkey = winreg.EnumKey(key, index)
    path = WIN_REGISTRY_PATH + "\\" + subkey

    if subkey == 'Properties':
        break

    # Check for adapter match for appropriate interface
    new_key = winreg.OpenKey(reg_hdl, path)
    try:
        adapterDesc = winreg.QueryValueEx(new_key, "DriverDesc")
        if adapterDesc[0] == target_device:
            adapter_path = path
            target_index = index
            break
        else:
            winreg.CloseKey(new_key)
    except (WindowsError) as err:
        if err.errno == 2:  # register value not found, ok to ignore
            pass
        else:
            raise err

if adapter_path is None:
    print 'Device not found.'
    winreg.CloseKey(key)
    winreg.CloseKey(reg_hdl)
    return
```
最后设置为用户需要的MAC地址
```python
adapter_key = winreg.OpenKey(reg_hdl, adapter_path, 0, winreg.KEY_WRITE)
winreg.SetValueEx(adapter_key, "NetworkAddress", 0, winreg.REG_SZ, new_mac)
```

### 重启相关设备 ###
设置成功之后，需要重启相应的设备才能看到修改后的MAC地址
```python
cmd = "wmic path win32_networkadapter where index=" + str(index) + " call disable"
subprocess.check_output(cmd)
cmd = "wmic path win32_networkadapter where index=" + str(index) + " call enable"
subprocess.check_output(cmd)
```
当然还有其他的命令行可以做到，可以参考这里：http://answers.microsoft.com/en-us/windows/forum/windows_7-hardware/enabledisable-network-interface-via-command-line/17a21634-c5dd-4038-bc0a-d739209f5081?auth=1


