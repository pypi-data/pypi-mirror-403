#!/usr/bin/env python3
# coding = utf8
"""
@ Author : ZeroSeeker
@ e-mail : zeroseeker@foxmail.com
@ GitHub : https://github.com/ZeroSeeker
@ Gitee : https://gitee.com/ZeroSeeker
"""
import subprocess
import ipaddress
import requests
import json
import re


def get_public_ip() -> str:
    """
    获取当前网络公网ip地址
    备用地址：http://www.3322.org/dyndns/getip
    """
    import requests
    import json
    origin_ip = ''
    try:
        request_url = "http://httpbin.org/ip"
        response = requests.get(url=request_url)
        origin_ip = json.loads(response.text).get("origin")
    finally:
        return origin_ip


def get_local_ip() -> str:
    """
    获取内网ip地址
    """
    import socket
    ip = ''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
        return ip


def get_ip() -> dict:
    """
    获取当前网络ip地址（含有公网ip和内网ip）
    """
    origin_ip = get_public_ip()  # 获取公网ip
    local_ip = get_local_ip()  # 获取内网ip
    return {'origin_ip': origin_ip, 'local_ip': local_ip}


def get_ip_addr(ip: str):
    """
    查询ip归属地
    """
    api_url = f'http://whois.pconline.com.cn/ipJson.jsp?ip={ip}&json=true'
    response = requests.get(api_url)
    response_text = response.text.replace("\\", "-")
    addr = json.loads(response_text)['addr']
    return addr


def ipv6_exploded(addr: str):
    """
    将压缩的地址扩展
    """
    # 将压缩的IPv6地址字符串转换为IPv6地址对象
    ipv6_obj = ipaddress.IPv6Address(addr)
    # 使用 `.exploded` 属性获取完整的扩展形式
    return ipv6_obj.exploded


def ipv6_compressed(addr: str):
    """
    将标准地址压缩
    """
    # 将压缩的IPv6地址字符串转换为IPv6地址对象
    ipv6_obj = ipaddress.IPv6Address(addr)
    # 使用 `.compressed` 属性可以获取标准的压缩形式（去除前导零，压缩连续的零段）
    return ipv6_obj.compressed


def check_ipv6_exploded(ipv6_str):
    try:
        addr_obj = ipaddress.IPv6Address(ipv6_str)
        is_exploded = (addr_obj.exploded == ipv6_str)
        return is_exploded
    except ipaddress.AddressValueError:
        print(f"错误: '{ipv6_str}' 不是一个有效的IPv6地址。")
        return False


class JsonIP:
    """
    https://jsonip.com

    类似的服务还有：
    ident.me

    """
    def __init__(self):
        self.ip = get_ip()
        self.ipv4 = self.get_ipv4()
        self.ipv6 = self.get_ipv6()

    @staticmethod
    def get_ip():
        try:
            # 使用 ident.me 的API服务
            response = requests.get('https://jsonip.com', timeout=5)
            response.raise_for_status()  # 检查请求是否成功
            return response.json().get("ip")
        except requests.exceptions.RequestException as e:
            print(f"通过API[https://jsonip.com]获取公网IP地址失败: {e}")
            return None

    @staticmethod
    def get_ipv4():
        try:
            # 使用 ident.me 的API服务
            response = requests.get('https://ipv4.jsonip.com', timeout=5)
            response.raise_for_status()  # 检查请求是否成功
            return response.json().get("ip")
        except requests.exceptions.RequestException as e:
            print(f"通过API[https://jsonip.com]获取公网IPv4地址失败: {e}")
            return None

    @staticmethod
    def get_ipv6():
        try:
            # 使用 ident.me 的API服务
            response = requests.get('https://ipv6.jsonip.com', timeout=5)
            response.raise_for_status()  # 检查请求是否成功
            return response.json().get("ip")
        except requests.exceptions.RequestException as e:
            print(f"通过API[https://jsonip.com]获取公网IPv6地址失败: {e}")
            return None

    def get_public_ip_address(
            self,
            ip: bool = True,
            ipv4: bool = False,
            ipv6: bool = False
    ):
        res = dict()
        if ip:
            res["ip"] = self.get_ip()
        if ipv4:
            res["ipv4"] = self.get_ipv4()
        if ipv6:
            res["ipv6"] = self.get_ipv6()
        return res


class IPw:
    """
    https://ipw.cn/

    """
    def __init__(self):
        self.ip = get_ip()
        self.ipv4 = self.get_ipv4()
        self.ipv6 = self.get_ipv6()

    @staticmethod
    def get_ip():
        try:
            # 使用 ident.me 的API服务
            response = requests.get('https://test.ipw.cn/api/ip/myip?json', timeout=5)
            response.raise_for_status()  # 检查请求是否成功
            return response.json().get("IP")
        except requests.exceptions.RequestException as e:
            print(f"通过API[https://ipw.cn/]获取公网IP地址失败: {e}")
            return None

    @staticmethod
    def get_ipv4():
        try:
            # 使用 ident.me 的API服务
            response = requests.get('https://4.ipw.cn/api/ip/myip?json', timeout=5)
            response.raise_for_status()  # 检查请求是否成功
            return response.json().get("IP")
        except requests.exceptions.RequestException as e:
            print(f"通过API[https://4.ipw.cn]获取公网IPv4地址失败: {e}")
            return None

    @staticmethod
    def get_ipv6():
        try:
            # 使用 ident.me 的API服务
            response = requests.get('https://6.ipw.cn/api/ip/myip?json', timeout=5)
            response.raise_for_status()  # 检查请求是否成功
            return response.json().get("IP")
        except requests.exceptions.RequestException as e:
            print(f"通过API[https://6.ipw.cn]获取公网IPv6地址失败: {e}")
            return None

    def get_public_ip_address(
            self,
            ip: bool = True,
            ipv4: bool = False,
            ipv6: bool = False
    ):
        res = dict()
        if ip:
            res["ip"] = self.get_ip()
        if ipv4:
            res["ipv4"] = self.get_ipv4()
        if ipv6:
            res["ipv6"] = self.get_ipv6()
        return res


class IPAddr:
    def __init__(self):
        pass

    @staticmethod
    def get_ipv6_from_ip_command():
        """
        通过解析ip命令获取详细的IPv6信息
        """
        ipv6_details = []

        try:
            # 执行ip -6 addr show命令获取详细信息
            result = subprocess.run(['/usr/sbin/ip', '-6', 'addr', 'show'],
                                    capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                # 尝试使用ifconfig作为备选
                return get_ipv6_from_ifconfig()

            output = result.stdout
            lines = output.split('\n')

            current_interface = None
            current_addr_info = {}

            for line in lines:
                # 匹配接口行，如: "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500"
                interface_match = re.match(r'^\d+:\s+([^:]+):\s+<([^>]+)>', line)
                if interface_match:
                    if current_interface and current_addr_info:
                        ipv6_details.append(current_addr_info.copy())
                        current_addr_info = {}

                    current_interface = interface_match.group(1)
                    flags = interface_match.group(2).split(',')

                    current_addr_info = {
                        'interface': current_interface,
                        'flags': flags,
                        'ipv6_addresses': []
                    }

                    # 提取MTU值
                    mtu_match = re.search(r'mtu\s+(\d+)', line)
                    if mtu_match:
                        current_addr_info['mtu'] = int(mtu_match.group(1))

                # 匹配IPv6地址行
                if current_interface:
                    # 匹配格式: inet6 2001:db8::1/64 scope global
                    ipv6_match = re.search(r'inet6\s+([a-f0-9:]+)(?:%[^/]+)?/(\d+)\s+scope\s+(\w+)',
                                           line, re.IGNORECASE)
                    if ipv6_match:
                        ipv6_addr = ipv6_match.group(1)
                        prefix_len = ipv6_match.group(2)
                        scope = ipv6_match.group(3)

                        addr_details = {
                            'address': ipv6_addr,
                            'prefix_length': int(prefix_len),
                            'scope': scope,
                            'type': classify_ipv6_address(ipv6_addr)
                        }

                        # 提取更多标志
                        if 'dynamic' in line:
                            addr_details['dynamic'] = True
                        if 'noprefixroute' in line:
                            addr_details['noprefixroute'] = True
                        if 'valid_lft' in line:
                            # 提取有效期信息
                            valid_match = re.search(r'valid_lft\s+(\w+)\s+preferred_lft\s+(\w+)', line)
                            if valid_match:
                                addr_details['valid_lft'] = valid_match.group(1)
                                addr_details['preferred_lft'] = valid_match.group(2)

                        current_addr_info['ipv6_addresses'].append(addr_details)

            # 添加最后一个接口的信息
            if current_interface and current_addr_info:
                ipv6_details.append(current_addr_info)

        except Exception as e:
            print(f"解析ip命令输出时出错: {e}")
            return get_ipv6_from_ifconfig()

        return ipv6_details

    @staticmethod
    def get_ipv6_from_ifconfig():
        """
        备选方法：使用ifconfig命令
        """
        ipv6_details = []

        try:
            result = subprocess.run(['/usr/sbin/ifconfig'], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                output = result.stdout
                interfaces = output.split('\n\n')

                for interface_block in interfaces:
                    lines = interface_block.split('\n')
                    if not lines or not lines[0]:
                        continue

                    # 提取接口名
                    interface_match = re.match(r'^(\S+)', lines[0])
                    if interface_match:
                        interface_name = interface_match.group(1)
                        interface_info = {
                            'interface': interface_name,
                            'ipv6_addresses': []
                        }

                        for line in lines:
                            # 匹配IPv6地址
                            ipv6_match = re.search(r'inet6\s+addr:\s*([a-f0-9:]+)', line, re.IGNORECASE)
                            if ipv6_match:
                                ipv6_addr = ipv6_match.group(1)
                                addr_details = {
                                    'address': ipv6_addr,
                                    'type': classify_ipv6_address(ipv6_addr)
                                }
                                interface_info['ipv6_addresses'].append(addr_details)

                        if interface_info['ipv6_addresses']:
                            ipv6_details.append(interface_info)

        except Exception as e:
            print(f"解析ifconfig输出时出错: {e}")

        return ipv6_details

    @staticmethod
    def classify_ipv6_address(ipv6_addr):
        """分类IPv6地址类型"""
        if ipv6_addr.startswith('fe80:'):
            return '链路本地地址'
        elif ipv6_addr.startswith('2000:'):
            return '全球单播地址'
        elif ipv6_addr.startswith('fc00:') or ipv6_addr.startswith('fd00:'):
            return '唯一本地地址'
        elif ipv6_addr == '::1':
            return '环回地址'
        elif ipv6_addr.startswith('ff00:'):
            return '组播地址'
        else:
            return '其他类型'

    @staticmethod
    def print_detailed_ipv6_info():
        """打印详细的IPv6信息"""
        ipv6_data = get_ipv6_from_ip_command()
        ipv6_real = None

        print("CentOS 7系统完整IPv6信息")
        print("=" * 100)

        if not ipv6_data:
            print("未找到IPv6地址信息")
            return

        for interface in ipv6_data:
            print(f"\n🔧 网络接口: {interface['interface']}")
            print(f"📊 接口标志: {', '.join(interface.get('flags', []))}")

            if 'mtu' in interface:
                print(f"📏 MTU: {interface['mtu']}")

            if interface['ipv6_addresses']:
                for i, addr in enumerate(interface['ipv6_addresses'], 1):
                    print(f"  📍 IPv6地址 #{i}:")
                    print(f"     地址: {addr['address']}")
                    print(f"     类型: {addr['type']}")
                    print(f"     前缀长度: /{addr.get('prefix_length', 'N/A')}")
                    print(f"     范围: {addr.get('scope', 'N/A')}")

                    address = addr['address']
                    if addr.get('scope', 'N/A') == "global" and addr.get('prefix_length', 'N/A') == 64:
                        ipv6_real = address

                    if 'dynamic' in addr:
                        print(f"     动态地址: 是")
                    if 'valid_lft' in addr:
                        print(f"     有效生存期: {addr.get('valid_lft', 'N/A')}")
                    if 'preferred_lft' in addr:
                        print(f"     首选生存期: {addr.get('preferred_lft', 'N/A')}")
            else:
                print("  该接口无IPv6地址")

            print("-" * 80)
        print("ipv6_real:", ipv6_real)
        return ipv6_real


if __name__ == '__main__':
    test = IPw()