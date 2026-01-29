# -*- coding: utf-8 -*-
"""
CFspider 本地代理服务器
支持双层代理（two_proxy），可供 v2ray 或浏览器使用
"""

import socket
import threading
import time
from urllib.parse import urlparse, quote


def generate_vless_link(
    cf_proxies: str,
    uuid: str,
    name: str = "CFspider",
    two_proxy: str = None
) -> dict:
    """
    生成 VLESS 导入链接
    
    Args:
        cf_proxies: Workers 地址，如 "https://your-workers.dev"
        uuid: VLESS UUID
        name: 节点名称
        two_proxy: 第二层代理（可选），格式 "host:port:user:pass"
    
    Returns:
        dict: {
            'vless_link': str,  # VLESS 链接（可导入 v2ray）
            'local_proxy_cmd': str,  # 启动本地代理的命令
            'note': str  # 使用说明
        }
    
    Example:
        >>> result = cfspider.generate_vless_link(
        ...     cf_proxies="https://your-workers.dev",
        ...     uuid="your-uuid",
        ...     two_proxy="us.cliproxy.io:3010:user:pass"
        ... )
        >>> print(result['vless_link'])
    """
    # 解析 Workers 地址
    parsed = urlparse(cf_proxies)
    if parsed.scheme:
        host = parsed.netloc or parsed.path.split('/')[0]
    else:
        host = cf_proxies.split('/')[0]
    
    # 生成基础 VLESS 链接（连接到 Workers）
    vless_params = {
        'security': 'tls',
        'type': 'ws',
        'host': host,
        'sni': host,
        'path': f'/{uuid}',
        'encryption': 'none'
    }
    
    params_str = '&'.join([f'{k}={quote(str(v))}' for k, v in vless_params.items()])
    vless_link = f"vless://{uuid}@{host}:443?{params_str}#{quote(name)}"
    
    result = {
        'vless_link': vless_link,
        'host': host,
        'uuid': uuid,
    }
    
    if two_proxy:
        # 解析第二层代理
        parts = two_proxy.split(':')
        if len(parts) >= 2:
            proxy_host = parts[0]
            proxy_port = parts[1]
            proxy_info = f"{proxy_host}:{proxy_port}"
            if len(parts) == 4:
                proxy_info += f" (user: {parts[2][:4]}***)"
        else:
            proxy_info = two_proxy
        
        # 生成本地代理启动命令
        result['local_proxy_cmd'] = (
            f'python -m cfspider.proxy_server '
            f'--cf-proxies "{cf_proxies}" '
            f'--uuid "{uuid}" '
            f'--two-proxy "{two_proxy}" '
            f'--port 1080'
        )
        
        result['note'] = f"""
=== 双层代理使用说明 ===

由于 VLESS 协议本身不支持代理链，有两种方式使用双层代理：

【方式 1】使用 CFspider 本地代理（推荐）
运行以下命令启动本地代理服务器：

{result['local_proxy_cmd']}

然后在浏览器或系统中配置代理为：
  HTTP/SOCKS5 代理: 127.0.0.1:1080

流量链路: 浏览器 → 本地代理(1080) → Workers(VLESS) → {proxy_info} → 目标网站

【方式 2】在 Workers 端配置 PROXYIP
1. 打开 Cloudflare Dashboard → Workers
2. 选择你的 Worker → Settings → Variables
3. 添加环境变量: PROXYIP = {parts[0] if len(parts) >= 2 else two_proxy}
4. 然后使用以下 VLESS 链接导入 v2ray：

{vless_link}

注意：方式 2 需要第二层代理支持无认证连接，或在 Workers 代码中配置认证。
"""
    else:
        result['note'] = f"""
=== VLESS 链接使用说明 ===

将以下链接导入 v2ray/clash 等客户端：

{vless_link}

流量链路: v2ray 客户端 → Workers(VLESS) → 目标网站
出口 IP: Cloudflare WARP 网络 IP
"""
    
    return result


class TwoProxyServer:
    """
    双层代理本地服务器
    
    提供 HTTP/SOCKS5 代理接口，内部通过 VLESS + two_proxy 实现
    """
    
    def __init__(
        self,
        cf_proxies: str,
        uuid: str,
        two_proxy: str = None,
        host: str = '127.0.0.1',
        port: int = 1080
    ):
        """
        初始化本地代理服务器
        
        Args:
            cf_proxies: Workers 地址
            uuid: VLESS UUID
            two_proxy: 第二层代理，格式 "host:port:user:pass"
            host: 监听地址（默认 127.0.0.1）
            port: 监听端口（默认 1080）
        """
        self.cf_proxies = cf_proxies
        self.uuid = uuid
        self.two_proxy = two_proxy
        self.host = host
        self.port = port
        self.server = None
        self.running = False
        self._vless_proxy = None
        self._vless_port = None
    
    def _ensure_vless_proxy(self):
        """确保 VLESS 代理已启动"""
        if self._vless_proxy is None:
            from .vless_client import LocalVlessProxy
            
            # 解析 Workers 地址
            parsed = urlparse(self.cf_proxies)
            if parsed.scheme:
                host = parsed.netloc or parsed.path.split('/')[0]
            else:
                host = self.cf_proxies.split('/')[0]
            
            vless_url = f"wss://{host}/{self.uuid}"
            print(f"[INIT] Starting VLESS proxy: {vless_url}")
            if self.two_proxy:
                print(f"[INIT] Two-proxy enabled: {self.two_proxy.split(':')[0]}:{self.two_proxy.split(':')[1]}")
            
            self._vless_proxy = LocalVlessProxy(vless_url, self.uuid, two_proxy=self.two_proxy)
            self._vless_port = self._vless_proxy.start()
            print(f"[INIT] VLESS proxy started on port {self._vless_port}")
    
    def start(self):
        """启动代理服务器"""
        self._ensure_vless_proxy()
        
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.server.listen(50)
        
        self.running = True
        
        print(f"=" * 60)
        print(f"CFspider Two-Proxy Server Started")
        print(f"=" * 60)
        print(f"Local Proxy:  {self.host}:{self.port}")
        print(f"Workers:      {self.cf_proxies}")
        if self.two_proxy:
            parts = self.two_proxy.split(':')
            print(f"Second Proxy: {parts[0]}:{parts[1]}")
        print(f"-" * 60)
        print(f"Configure your browser/system proxy to: {self.host}:{self.port}")
        print(f"Press Ctrl+C to stop")
        print(f"=" * 60)
        
        try:
            while self.running:
                try:
                    self.server.settimeout(1)
                    client, addr = self.server.accept()
                    handler = threading.Thread(
                        target=self._handle_client,
                        args=(client,),
                        daemon=True
                    )
                    handler.start()
                except socket.timeout:
                    continue
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.stop()
    
    def _handle_client(self, client):
        """处理客户端连接，转发到内部 VLESS 代理"""
        client_addr = None
        try:
            client_addr = client.getpeername()
            client.settimeout(30)
            
            # 连接到内部 VLESS 代理
            vless_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            vless_sock.settimeout(30)
            vless_sock.connect(('127.0.0.1', self._vless_port))
            
            print(f"[CONN] {client_addr} -> VLESS proxy :{self._vless_port}")
            
            # 双向转发
            stop_event = threading.Event()
            
            def forward(src, dst, name):
                try:
                    while not stop_event.is_set():
                        try:
                            src.settimeout(1)
                            data = src.recv(8192)
                            if not data:
                                break
                            dst.sendall(data)
                        except socket.timeout:
                            continue
                        except Exception as e:
                            break
                except Exception as e:
                    pass
                finally:
                    stop_event.set()
            
            t1 = threading.Thread(target=forward, args=(client, vless_sock, "C->V"), daemon=True)
            t2 = threading.Thread(target=forward, args=(vless_sock, client, "V->C"), daemon=True)
            t1.start()
            t2.start()
            
            # 等待任一方向结束
            while not stop_event.is_set():
                time.sleep(0.1)
            
            print(f"[CLOSE] {client_addr}")
            
        except Exception as e:
            print(f"[ERROR] {client_addr}: {e}")
        finally:
            try:
                client.close()
            except:
                pass
            try:
                vless_sock.close()
            except:
                pass
    
    def stop(self):
        """停止服务器"""
        self.running = False
        if self.server:
            try:
                self.server.close()
            except:
                pass
        if self._vless_proxy:
            try:
                self._vless_proxy.stop()
            except:
                pass


def start_proxy_server(
    cf_proxies: str,
    uuid: str,
    two_proxy: str = None,
    host: str = '127.0.0.1',
    port: int = 1080
):
    """
    启动本地代理服务器
    
    Args:
        cf_proxies: Workers 地址
        uuid: VLESS UUID
        two_proxy: 第二层代理（可选）
        host: 监听地址（默认 127.0.0.1）
        port: 监听端口（默认 1080）
    
    Example:
        >>> cfspider.start_proxy_server(
        ...     cf_proxies="https://your-workers.dev",
        ...     uuid="your-uuid",
        ...     two_proxy="us.cliproxy.io:3010:user:pass",
        ...     port=1080
        ... )
    """
    server = TwoProxyServer(cf_proxies, uuid, two_proxy, host, port)
    server.start()


# 命令行入口
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='CFspider Two-Proxy Server')
    parser.add_argument('--cf-proxies', required=True, help='Workers address')
    parser.add_argument('--uuid', required=True, help='VLESS UUID')
    parser.add_argument('--two-proxy', help='Second layer proxy (host:port:user:pass)')
    parser.add_argument('--host', default='127.0.0.1', help='Listen host (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=1080, help='Listen port (default: 1080)')
    
    args = parser.parse_args()
    
    start_proxy_server(
        cf_proxies=args.cf_proxies,
        uuid=args.uuid,
        two_proxy=args.two_proxy,
        host=args.host,
        port=args.port
    )

