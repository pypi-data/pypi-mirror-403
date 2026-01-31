#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRP - Python Registry Provider
A tool for managing Python package index sources.
"""

import os
import re
import sys
import json
import time
import argparse
import configparser
from urllib.parse import urlparse
import urllib.request
import urllib.error

# 定义版本
__version__ = "1.0.15"

# 默认源配置常量
DEFAULT_SOURCES = {
    "pypi": {
        "url": "https://pypi.org/simple/",
        "home": "https://pypi.org",
        "name": "pypi"
    },
    "pypi-test": {
        "url": "https://test.pypi.org/simple/",
        "home": "https://test.pypi.org",
        "name": "pypi-test"
    },
    "tuna": {
        "url": "https://pypi.tuna.tsinghua.edu.cn/simple/",
        "home": "https://pypi.tuna.tsinghua.edu.cn",
        "name": "tuna"
    },
    "aliyun": {
        "url": "https://mirrors.aliyun.com/pypi/simple/",
        "home": "https://mirrors.aliyun.com",
        "name": "aliyun"
    },
    "douban": {
        "url": "https://pypi.douban.com/simple/",
        "home": "https://pypi.douban.com",
        "name": "douban"
    },
    "huawei": {
        "url": "https://mirrors.huaweicloud.com/repository/pypi/simple/",
        "home": "https://mirrors.huaweicloud.com/",
        "name": "huawei"
    },
    "ustc": {
        "url": "https://pypi.mirrors.ustc.edu.cn/simple/",
        "home": "https://mirrors.ustc.edu.cn/",
        "name": "ustc"
    }
}


class PRP:
    def __init__(self):
        self.config_file = os.path.expanduser("~/.prp/config.json")
        # 使用实际的pip配置文件路径
        self.pip_config_file = self.get_pip_config_path()
        self.ensure_config_exists()
        self.load_registries()

    def get_pip_config_path(self):
        """获取实际的pip配置文件路径"""
        if sys.platform.startswith("win"):
            # Windows系统的pip配置文件路径
            config_path = os.path.expandvars("%APPDATA%/pip/pip.ini")
        else:
            # Mac/Linux系统的pip配置文件路径
            config_path = os.path.expanduser("~/.config/pip/pip.conf")
        
        # 检查配置文件是否存在，如果不存在，尝试其他可能的路径
        if not os.path.exists(config_path):
            # 检查备用路径
            alt_config_path = os.path.expanduser("~/.pip/pip.conf")  # Linux/macOS备用路径
            if sys.platform.startswith("win"):
                alt_config_path = os.path.expandvars("%APPDATA%\\pip\\pip.conf")  # Windows备用路径
            
            if os.path.exists(alt_config_path):
                return alt_config_path
        
        return config_path

    def ensure_config_exists(self):
        """确保配置文件存在"""
        # 优先获取pip配置文件是否存在并获取当前镜像源
        current_source_url = self.get_current_source_from_pip_config()
        config_dir = os.path.dirname(self.config_file)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        if not os.path.exists(self.config_file):
            # 创建默认配置
            default_config = {
                "registries": DEFAULT_SOURCES.copy(),
                "current_registry": "pypi",
                "extra_registries": []
            }
            self.registries = default_config['registries']
            if current_source_url:
                current_registry_name_list = self.get_name_from_url(current_source_url, default_config)
                if len(current_registry_name_list) > 0:
                    current_registry_name = current_registry_name_list[0]
                else:
                    current_registry_name = self.generate_auto_registry_name(current_source_url)
                # add registry
                default_config['registries'][current_registry_name] = {
                    'url': current_source_url,
                    'home': self.extract_homepage(current_source_url),
                    'name': current_registry_name
                }
                default_config['current_registry'] = current_registry_name
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
        else:
            # check if the config file exists
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 添加缺失的默认源
                for source_name, source_info in DEFAULT_SOURCES.items():
                    if source_name not in config['registries']:
                        config['registries'][source_name] = source_info
                        
                self.registries = config['registries']
            if current_source_url:
                current_registry_name_list = self.get_name_from_url(current_source_url, config)
                if len(current_registry_name_list) > 0:
                    current_registry_name = current_registry_name_list[0]
                else:
                    current_registry_name = self.generate_auto_registry_name(current_source_url)
                # add registry
                config['registries'][current_registry_name] = {
                    'url': current_source_url,
                    'home': self.extract_homepage(current_source_url),
                    'name': current_registry_name
                }
                config['current_registry'] = current_registry_name
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)

    def load_registries(self):
        """加载包镜像源配置"""
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            self.registries = config['registries']
            self.current_registry = config.get('current_registry', 'pypi')
            self.extra_registries = config.get('extra_registries', [])

    def save_config(self):
        """保存配置"""
        config = {
            'registries': self.registries,
            'current_registry': self.current_registry,
            'extra_registries': getattr(self, 'extra_registries', [])
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def list_registries(self):
        """列出所有包镜像源"""
        current_name = self.current_registry
        extra_registries = getattr(self, 'extra_registries', [])
        print("\nAvailable Registries:")
        for name, info in self.registries.items():
            if name == current_name:
                marker = " * "
            elif name in extra_registries:
                marker = " + "
            else:
                marker = "   "
            print(f"{marker} {name:<10} {info['url']}")
        print("\n* Current Registry")
        print("+ Extra Registry\n")

    def add_registry(self, *args):
        """添加新的包镜像源（支持多个）"""
        # 参数应该是 name1 url1 [home1] name2 url2 [home2] ... 的格式
        i = 0
        registries_to_add = []
        
        while i < len(args):
            # 至少需要name和url
            if i + 1 >= len(args):
                print("Missing URL for registry name:", args[i])
                return
                
            name = args[i]
            url = args[i + 1]
            
            # 检查是否存在可选的home参数
            home = None
            if i + 2 < len(args) and self.is_valid_url_with_protocol(args[i + 2]):
                # 第三个参数是home
                home = args[i + 2]
                i += 3  # 跳过name、url、home
            else:
                # 第三个参数是下一个name或不存在
                i += 2  # 跳过name、url
            
            # 验证参数
            if name in self.registries:
                print(f"Registry '{name}' already exists.")
                continue
                
            if not self.is_valid_url(url):
                print(f"Invalid URL: {url}")
                continue
                
            if len(list(filter(lambda x: urlparse(url).netloc in x['url'], self.registries.values()))) > 0:
                print(f"Netloc '{urlparse(url).netloc}' is already used by another registry.")
                continue
                
            home = self.extract_homepage(url) if home is None else home
            if len(list(filter(lambda x: home in x['home'], self.registries.values()))) > 0:
                print(f"Home '{home}' is already used by another registry.")
                continue
                
            if not url.endswith('/'):
                url += '/'
                
            registries_to_add.append((name, url, home))
        
        # 添加所有有效的镜像源
        for name, url, home in registries_to_add:
            self.registries[name] = {
                "url": url,
                "home": home,
                "name": name
            }
            print(f"Registry '{name}' added successfully.")
        
        if registries_to_add:
            self.save_config()

    def delete_registry(self, *names):
        """删除包镜像源（支持多个）"""
        if not names:
            print("Please specify at least one registry name to delete.")
            return
            
        # 检查是否尝试删除所有镜像源
        registries_to_delete = []
        for name in names:
            if name not in self.registries:
                print(f"Registry '{name}' does not exist.")
                continue
            registries_to_delete.append(name)
        
        # 检查是否尝试删除默认源
        for name in registries_to_delete:
            if name in DEFAULT_SOURCES:
                print(f"Cannot delete default registry '{name}'. Default registries are protected.")
                registries_to_delete.remove(name)
        
        if len(self.registries) <= len(registries_to_delete):
            print("Cannot delete all registries. At least one registry must remain.")
            return
        
        # 执行删除
        deleted_names = []
        for name in registries_to_delete:
            del self.registries[name]
            deleted_names.append(name)
            
            # 如果删除的是当前使用的镜像源，则需要重新设置
            if self.current_registry == name:
                # 从额外镜像源中找一个作为新的当前镜像源
                available_extra = [reg for reg in getattr(self, 'extra_registries', []) if reg in self.registries]
                if available_extra:
                    self.current_registry = available_extra[0]
                    # 从额外镜像源中移除新的当前镜像源
                    self.extra_registries = [reg for reg in getattr(self, 'extra_registries', []) if reg != self.current_registry and reg in self.registries]
                else:
                    # 如果额外镜像源中没有可用的，则从剩余镜像源中选择第一个
                    self.current_registry = next(iter(self.registries))
                    self.extra_registries = []
                    
                # 更新pip配置
                self.update_pip_config()
                print(f"You deleted the current registry, set to {self.current_registry}")
        
        # 更新额外镜像源列表，移除已被删除的
        if hasattr(self, 'extra_registries'):
            self.extra_registries = [reg for reg in getattr(self, 'extra_registries', []) if reg in self.registries]
        
        self.save_config()
        for name in deleted_names:
            print(f"Registry '{name}' deleted successfully.")

    def use_registry(self, *names):
        """切换到指定包镜像源并更新pip配置（支持多个源）"""
        if not names:
            print("Please specify at least one registry name.")
            return False
            
        # 验证所有提供的镜像源名称是否存在
        for name in names:
            if name not in self.registries:
                print(f"Registry '{name}' does not exist.")
                return False
        
        # 第一个作为主要镜像源
        primary_registry = names[0]
        additional_registries = names[1:]  # 其余的作为额外镜像源
        
        self.current_registry = primary_registry
        self.extra_registries = additional_registries
        
        self.save_config()
        
        # 更新pip配置文件
        success = self.update_pip_config()
        if success:
            primary_url = self.registries[primary_registry]['url']
            print(f"Successfully switched to registry '{primary_registry}': {primary_url}")
            if additional_registries:
                additional_urls = [self.registries[name]['url'] for name in additional_registries]
                print(f"With additional registries: {', '.join(additional_urls)}")
            print("pip will now use these registries by default.")
            return True
        else:
            print(f"Failed to update pip configuration.")
            return False

    def update_pip_config(self):
        """更新pip配置文件以使用当前选定的包镜像源和额外镜像源"""
        registry_url = self.registries[self.current_registry]['url']
        
        # 获取额外镜像源的URL列表
        extra_urls = []
        for reg_name in getattr(self, 'extra_registries', []):
            if reg_name in self.registries:
                extra_urls.append(self.registries[reg_name]['url'])
        
        # 提取所有主机名用于 trusted-host
        all_urls = [registry_url] + extra_urls
        host_names = []
        for url in all_urls:
            parsed_url = urlparse(url)
            host_name = parsed_url.netloc
            if host_name not in host_names:
                host_names.append(host_name)
        
        # 确保目录存在
        pip_config_dir = os.path.dirname(self.pip_config_file)
        if not os.path.exists(pip_config_dir):
            os.makedirs(pip_config_dir)
        
        # 创建 configparser 对象
        config = configparser.ConfigParser()
        
        # 如果配置文件存在，读取它
        if os.path.exists(self.pip_config_file):
            config.read(self.pip_config_file, encoding='utf-8')
        
        # 确保 [global] 部分存在
        if not config.has_section('global'):
            config.add_section('global')
        
        # 设置 index-url
        config.set('global', 'index-url', registry_url)
        
        # 设置 extra-index-url（如果有额外的镜像源）
        if extra_urls:
            extra_index_urls = '\n\t'.join(extra_urls)
            config.set('global', 'extra-index-url', extra_index_urls)
        
        # 确保 [install] 部分存在
        if not config.has_section('install'):
            config.add_section('install')
        
        # 设置 trusted-host
        if host_names:
            trusted_hosts = '\n\t'.join(host_names)
            config.set('install', 'trusted-host', trusted_hosts)
        
        # 写入配置文件
        with open(self.pip_config_file, 'w', encoding='utf-8') as f:
            config.write(f)
        
        return True

    def test_registry_speed(self, name=None):
        """测试包镜像源速度"""
        if name:
            registries_to_test = {name: self.registries[name]} if name in self.registries else {}
        else:
            registries_to_test = self.registries

        print(f"\nTesting registry speeds...")
        results = []
        
        for reg_name, info in registries_to_test.items():
            url = info['url']
            start_time = time.time()
            try:
                # 使用urllib替换requests
                req = urllib.request.Request(url, method="HEAD")
                req.add_header('User-Agent', 'Mozilla/5.0 (PRP Test)')
                
                # 发起请求并计算响应时间
                response = urllib.request.urlopen(req, timeout=5)
                end_time = time.time()
                response_time = round((end_time - start_time) * 1000, 2)
                
                # 检查是否可以访问
                status = "OK" if response.getcode() in [200, 403] else str(response.getcode())
                results.append((reg_name, response_time, status))
                
            except urllib.error.HTTPError as e:
                # 处理HTTP错误
                end_time = time.time()
                response_time = round((end_time - start_time) * 1000, 2)
                results.append((reg_name, response_time, f"HTTP Error: {e.code}"))
            except urllib.error.URLError as e:
                # 处理URL错误（如连接失败）
                results.append((reg_name, float('inf'), f"Connection Error: {str(e.reason)}"))
            except Exception as e:
                # 处理其他异常
                results.append((reg_name, float('inf'), f"Error: {str(e)}"))
        
        # 按响应时间排序
        results.sort(key=lambda x: x[1] if isinstance(x[1], (int, float)) else float('inf'))
        
        print(f"\n{'Registry':<10} {'Response Time (ms)':<20} {'Status':<10}")
        print("-" * 45)
        for name, response_time, status in results:
            rt_str = f"{response_time}ms" if isinstance(response_time, (int, float)) else "N/A"
            print(f"{name:<10} {rt_str:<20} {status:<10}")

    def current_registry_info(self):
        """显示当前包镜像源信息"""
        # 首先检查pip配置文件中的实际设置
        actual_source = self.get_current_source_from_pip_config()
        
        if actual_source:
            # 查找匹配的镜像名称
            matched_registry_name = None
            for name, info in self.registries.items():
                if info['url'].rstrip('/') == actual_source.rstrip('/'):
                    matched_registry_name = name
                    break
            
            if matched_registry_name:
                print(f"Current registry: {matched_registry_name}")
                print(f"URL: {actual_source}")
                print("(Detected from pip configuration)")
            else:
                # 如果不在镜像中，自动添加
                auto_name = self.generate_auto_registry_name(actual_source)
                self.registries[auto_name] = {
                    "url": actual_source,
                    "home": self.extract_homepage(actual_source),
                    "name": auto_name
                }
                self.save_config()
                
                print(f"Current registry: {auto_name}")
                print(f"URL: {actual_source}")
                print(f"(Automatically added from pip configuration as {auto_name})")
        else:
            # 如果无法从pip配置中获取，使用内部配置
            if self.current_registry in self.registries:
                info = self.registries[self.current_registry]
                print(f"Current registry: {self.current_registry}")
                print(f"URL: {info['url']}")
            else:
                print("No current registry set.")
        
        print(f"Configured in pip: {self.pip_config_file}")

    def get_name_from_url(self, url, registries_dict):
        """从字典对象中通过url查找name值"""
        return list(filter(lambda x: registries_dict['registries'][x]['url'] == url, registries_dict['registries'].keys()))
    
    def extract_homepage(self, url):
        """从URL提取主页地址"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def generate_auto_registry_name(self, url):
        """从URL中提取合适的名称，通过分割域名的方式"""

        # 解析URL获取主机名
        parsed = urlparse(url)
        hostname = parsed.netloc.lower()
        
        # 按照点分割域名
        parts = hostname.split('.')
        
        # 定义需要忽略的关键词
        skip_parts = {'pypi', 'mirror', 'mirrors'}
        
        # 按照默认顺序查找第一个不是skip_parts中的部分
        candidate_name = None
        for part in parts:
            if part not in skip_parts:
                candidate_name = part.replace('pypi', '').replace('mirror', '').replace('mirrors', '')
                break
        
        # 如果仍然找不到合适的名称，使用整个主机名作为基础
        if not candidate_name:
            candidate_name = hostname.replace('.', '_')
        
        # 确保名称不与现有名称冲突
        final_name = candidate_name
        counter = 0
        while final_name in self.registries:
            final_name = f"{candidate_name}{counter}"
            counter += 1
            
        return final_name

    def get_current_source_from_pip_config(self):
        """从pip配置文件中获取当前设置的镜像源"""
        if not os.path.exists(self.pip_config_file):
            return None
        
        try:
            config = configparser.ConfigParser()
            config.read(self.pip_config_file, encoding='utf-8')
            
            if config.has_option('global', 'index-url'):
                return config.get('global', 'index-url')
            
            return None
        except Exception:
            # 如果读取配置文件出现问题，返回None
            return None

    def is_valid_url(self, url):
        """检查URL是否有效"""
        url_regex = re.compile(
            r'^(?:http|ftp)s?://'  # 协议（http, https, ftp）
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # 域名
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # IP 地址
            r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # IPv6
            r'(:\d+)?(\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])?$', re.IGNORECASE)  # 端口和路径

        return bool(url_regex.match(url))

    def is_valid_url_with_protocol(self, url):
        """检查URL是否以协议开头（用于区分URL和名称）"""
        return url.startswith(('http://', 'https://', 'ftp://', 'ftps://'))

    def reset_to_defaults(self):
        """恢复默认配置"""
        default_config = {
            "registries": DEFAULT_SOURCES.copy(),
            "current_registry": "pypi",
            "extra_registries": []
        }
        
        # 更新实例变量
        self.registries = default_config['registries']
        self.current_registry = default_config['current_registry']
        self.extra_registries = default_config['extra_registries']
        
        # 保存配置
        self.save_config()
        
        # 更新pip配置
        self.update_pip_config()
        
        print("已恢复默认配置")
        return True

    def check_and_set_fastest_mirror_if_needed(self):
        """检查是否需要自动设置最快镜像源（仅在首次运行或重置后）"""
        # 现在我们不再自动执行此操作，只保留方法以备其他用途
        pass

    def get_fastest_n_registries(self, n):
        """获取最快的N个镜像源，返回按速度排序的(name, info)元组列表"""
        registries_to_test = self.registries  # 测试所有镜像源

        # 创建一个列表存储 (registry_name, response_time) 的元组
        results = []
        
        print(f"正在测试 {len(registries_to_test)} 个镜像源的速度...")
        
        for reg_name, info in registries_to_test.items():
            url = info['url']
            start_time = time.time()
            try:
                # 使用urllib替换requests
                req = urllib.request.Request(url, method="HEAD")
                req.add_header('User-Agent', 'Mozilla/5.0 (PRP Auto-Detection)')
                
                # 发起请求并计算响应时间
                response = urllib.request.urlopen(req, timeout=10)
                end_time = time.time()
                response_time = round((end_time - start_time) * 1000, 2)
                
                print(f"  {reg_name}: {response_time}ms")
                
                # 添加到结果列表
                results.append((reg_name, response_time, info))
                
            except urllib.error.HTTPError as e:
                print(f"  {reg_name}: HTTP Error {e.code}")
                # 对于HTTP错误，给予一个很大的响应时间
                results.append((reg_name, float('inf'), info))
            except urllib.error.URLError as e:
                print(f"  {reg_name}: Connection Error ({str(e.reason)})")
                # 对于连接错误，给予一个很大的响应时间
                results.append((reg_name, float('inf'), info))
            except Exception as e:
                print(f"  {reg_name}: Error ({str(e)})")
                # 对于其他错误，给予一个很大的响应时间
                results.append((reg_name, float('inf'), info))
        
        # 按响应时间排序
        results.sort(key=lambda x: x[1])
        
        # 返回前n个最快的镜像源的(name, info)元组
        return [(name, info) for name, _, info in results[:n]]
    
    def find_fastest_registry(self):
        """找出最快的镜像源"""
        registries_to_test = self.registries

        fastest_name = None
        min_response_time = float('inf')
        
        print(f"正在测试 {len(registries_to_test)} 个镜像源的速度...")
        
        for reg_name, info in registries_to_test.items():
            url = info['url']
            start_time = time.time()
            try:
                # 使用urllib替换requests
                req = urllib.request.Request(url, method="HEAD")
                req.add_header('User-Agent', 'Mozilla/5.0 (PRP Auto-Detection)')
                
                # 发起请求并计算响应时间
                response = urllib.request.urlopen(req, timeout=10)
                end_time = time.time()
                response_time = round((end_time - start_time) * 1000, 2)
                
                print(f"  {reg_name}: {response_time}ms")
                
                # 检查是否是最快的
                if response_time < min_response_time:
                    min_response_time = response_time
                    fastest_name = reg_name
                
            except urllib.error.HTTPError as e:
                print(f"  {reg_name}: HTTP Error {e.code}")
            except urllib.error.URLError as e:
                print(f"  {reg_name}: Connection Error ({str(e.reason)})")
            except Exception as e:
                print(f"  {reg_name}: Error ({str(e)})")
        
        return fastest_name

def main():
    epilog_text = """
实例(Examples):
  prp ls                           列出所有镜像源(List all registries)
  prp use                          自动检测并切换到最快的镜像源(Auto-detect and switch to the fastest registry)
  prp use tuna                     切换镜像源为tuna(Switch to TUNA mirror)
  prp use aliyun tuna pypi         切换到aliyun为主源，同时使用tuna和pypi作为额外源(Switch to aliyun as main with tuna and pypi as extras)
  prp use 1                        将所有镜像源按网速快慢排序，选择最快的1个镜像源作为主源(Sort all sources by speed, select the fastest 1 source as main source)
  prp use 2                        将所有镜像源按网速快慢排序，选择最快的2个镜像源，第一个为主源，第二个为备用源(Sort all sources by speed, select the fastest 2 sources, first as main, second as backup)
  prp use 3                        将所有镜像源按网速快慢排序，选择最快的3个镜像源，第一个为主源，其余为备用源(Sort all sources by speed, select the fastest 3 sources, first as main, rest as backups)
  prp use N                        将所有镜像源按网速快慢排序，选择最快的N个镜像源(N is number selecting top N fastest sources by speed)
  prp add name1 url1 [home1] name2 url2 [home2]    添加多个镜像源(Add multiple registries)
  prp del tuna                     删除特定镜像源(Delete a registry)
  prp del tuna aliyun              删除多个镜像源(Delete multiple registries)
  prp reset                        恢复默认配置(Reset to default configuration)
  prp test                         测试所有镜像源速度(Test registry speeds)
  prp test tuna                    测试特定镜像源速度(Test registry speeds)
  prp current                      查看当前镜像源(Show current registry)
  prp version                      查看版本信息(Show version)

获取更多帮助信息，浏览：https://github.com/xiaobaiOTS/xiaobai-prp
For more information, visit: https://github.com/xiaobaiOTS/xiaobai-prp
    """.strip()
    parser = argparse.ArgumentParser(
        prog='prp',
        description=f'PRP (Python Registry Provider) \n版本：{__version__} \n是一个用于管理 Python 包镜像源的工具\nby 807447312@qq.com',
        epilog=epilog_text,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令(Available commands)')
    
    # List command
    subparsers.add_parser('ls', help='列出所有镜像源(List all registries)')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='添加新的镜像源(Add a new registry)')
    add_parser.add_argument('args', nargs='+', help='镜像源名称、URL和可选主页列表(Registry name, URL and optional homepage list, e.g., name1 url1 [home1] name2 url2 [home2])')
    
    # Delete command
    del_parser = subparsers.add_parser('del', help='删除包镜像源(Delete a registry)')
    del_parser.add_argument('name', nargs='+', help='要删除的包镜像源名称(Registry names to delete, space separated)')
    
    # Reset command
    subparsers.add_parser('reset', help='恢复默认配置(Reset to default configuration)')
    
    # Use command
    use_parser = subparsers.add_parser('use', help='切换到指定镜像源(Switch to a registry)')
    use_parser.add_argument('name', nargs='*', help='要切换到的镜像源名称(Registry names to switch to, space separated, first is primary)，或输入数字N选择前N个最快的源，按网速快慢排序(N is number selecting top N fastest sources by speed)')
    use_parser.add_argument('--fastest', action='store_true', help='自动检测并切换到最快的镜像源(Auto-detect and switch to the fastest registry)')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='测试镜像源速度(Test registry speed)')
    test_parser.add_argument('name', nargs='?', help='要测试的特定镜像源名称(可选)(Specific registry name to test (optional))')
    
    # Current command
    subparsers.add_parser('current', help='显示当前镜像源(Show current registry)')

    subparsers.add_parser('version', help='显示当前版本(Show current version)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    prp = PRP()
    
    if args.command == 'ls':
        prp.list_registries()
    elif args.command == 'add':
        prp.add_registry(*args.args)
    elif args.command == 'del':
        prp.delete_registry(*args.name)
    elif args.command == 'reset':
        prp.reset_to_defaults()
    elif args.command == 'use':
        if hasattr(args, 'fastest') and args.fastest:
            # 如果指定了--fastest参数，自动找到最快的镜像源并切换
            fastest = prp.find_fastest_registry()
            if fastest:
                print(f"检测到最快的镜像源是: {fastest}")
                prp.use_registry(fastest)
            else:
                print("未能检测到可用的镜像源")
        elif not args.name:
            # 如果没有指定参数，等效于 --fastest
            fastest = prp.find_fastest_registry()
            if fastest:
                print(f"检测到最快的镜像源是: {fastest}")
                prp.use_registry(fastest)
            else:
                print("未能检测到可用的镜像源")
        elif len(args.name) == 1 and args.name[0].isdigit():
            # 如果是单个数字参数，表示选择前N个最快的源
            n = int(args.name[0])
            if n < 1:
                print(f"错误: 数字必须大于等于1，输入的值: {n}")
                return
            if n > len(prp.registries):
                print(f"错误: 输入的数字 {n} 超出了可用镜像源的数量范围 (1-{len(prp.registries)})")
                return
                
            # 获取最快的N个镜像源
            sorted_registries = prp.get_fastest_n_registries(n)
            if sorted_registries:
                registry_names = [reg[0] for reg in sorted_registries]  # 取出名称
                registry_info_str = ', '.join([f'{name}({info["url"]})' for name, info in sorted_registries])
                print(f"按网速快慢排序的前{n}个镜像源: {registry_info_str}")
                prp.use_registry(*registry_names)
            else:
                print("未能获取到可用的镜像源")
        else:
            prp.use_registry(*args.name)
    elif args.command == 'test':
        prp.test_registry_speed(args.name)
    elif args.command == 'current':
        prp.current_registry_info()
    elif args.command == 'version':
        print(__version__)


if __name__ == '__main__':
    main()