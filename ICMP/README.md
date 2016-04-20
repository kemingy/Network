# ICMP协议Ping方法的Python实现解析 #

## 说明 ##

* 本代码适合Windows，没有在其他系统下进行测试
* 参考对象为https://github.com/samuel/python-ping

## 流程 ##

1. 选择目标网址
2. 解析对方ip地址
3. 构造数据报，添加校验和，发送并记录发送时间
4. 循环监听，直到接收到数据报，提取对方发送时间，获得数据报传输时间；若超时则返回None

## 细节解析 ##

### 检查管理员权限 ###

```python
if ctypes.windll.shell32.IsUserAnAdmin() == 0:
    print 'Sorry! You should run this with administrative privileges.'
    sys.exit()
```

### 获取本机IP ###

```python
my_ID = os.getpid() & 0xFFFF
```

### 构造Socket ###

```python
icmp = socket.getprotobyname('icmp')
my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
```

### 构造数据报 ###

```python
data = (192 - byte_in_double) * "P"
data = struct.pack("d", time.clock()) + data
header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), ID, 1)
packet = header + data
```

### 计算校验和 ###

```python
checksum = 0
count = (len(source) / 2) * 2
i = 0
while i < count:
    temp = ord(source[i + 1]) * 256 + ord(source[i]) # 256 = 2^8
    checksum = checksum + temp
    checksum = checksum & 0xffffffff # 4,294,967,296 (2^32)
    i = i + 2

if i < len(source):
    checksum = checksum + ord(source[len(source) - 1])
    checksum = checksum & 0xffffffff

# 32-bit to 16-bit
checksum = (checksum >> 16) + (checksum & 0xffff)
checksum = checksum + (checksum >> 16)
answer = ~checksum
answer = answer & 0xffff

# why? ans[9:16 1:8]
answer = answer >> 8 | (answer << 8 & 0xff00)
```

### 提取信息，计算发送时长 ###

```python
time_received = time.clock()
# socket.recvfrom(bufsize[, flags])
# The return value is a pair (string, address)
rec_packet, addr = my_socket.recvfrom(1024)
icmp_header = rec_packet[20 : 28]
ip_type, code, checksum, packet_ID, sequence = struct.unpack("bbHHh", icmp_header)
if ip_type != 8 and packet_ID == ID: # ip_type should be 0
    byte_in_double = struct.calcsize("d")
    time_sent = struct.unpack("d", rec_packet[28 : 28 + byte_in_double])[0]
    return time_received - time_sent
```
