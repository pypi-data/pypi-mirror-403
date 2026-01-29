import logging
from n4 import N4Client, N4Error

import socket
import threading
import logging
import time

class P2pClient:
    def __init__(self, local_src_port: int, peer_ip: str, peer_port: int):
        self.local_src_port = local_src_port
        self.peer_ip = peer_ip
        self.peer_port = peer_port
        self.sock = None

    def connect(self):
        """创建UDP socket连接到对端"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', self.local_src_port))
        logging.info(f"已绑定本地端口 {self.local_src_port}")
        return self.sock

    def send_message(self, message: str):
        """发送消息到对端"""
        if not self.sock:
            self.connect()

        data = message.encode('utf-8')
        self.sock.sendto(data, (self.peer_ip, self.peer_port))
        logging.info(f"发送消息到 {self.peer_ip}:{self.peer_port}: {message}")

    def receive_messages(self, timeout=10):
        """接收消息（阻塞模式）"""
        if not self.sock:
            self.connect()

        logging.info(f"开始监听来自 {self.peer_ip}:{self.peer_port} 的消息...")

        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                self.sock.settimeout(2)  # 设置超时以便可以检查时间
                data, addr = self.sock.recvfrom(1024)
                if addr[0] == self.peer_ip:
                    message = data.decode('utf-8', errors='ignore')
                    logging.info(f"收到来自 {addr[0]}:{addr[1]} 的消息: {message}")
            except socket.timeout:
                continue
            except Exception as e:
                logging.error(f"接收消息出错: {e}")
                break

def interactive_mode(client: P2pClient):
    """交互模式：用户可以输入消息发送"""
    # 启动接收线程
    recv_thread = threading.Thread(target=client.receive_messages, args=(30,))
    recv_thread.daemon = True
    recv_thread.start()

    print("\n" + "="*50)
    print("P2P通信测试")
    print("="*50)
    print(f"本地端口: {client.local_src_port}")
    print(f"对端地址: {client.peer_ip}:{client.peer_port}")
    print("输入 'exit' 退出")
    print("="*50 + "\n")

    try:
        while True:
            message = input("请输入要发送的消息: ").strip()
            if message.lower() == 'exit':
                break
            if message:
                client.send_message(message)
    except KeyboardInterrupt:
        print("\n程序退出")
    except Exception as e:
        logging.error(f"错误: {e}")

def auto_test_mode(client: P2pClient, num_messages=5):
    """自动测试模式：发送测试消息"""
    print("\n" + "="*50)
    print("P2P自动测试模式")
    print("="*50)

    # 启动接收线程
    recv_thread = threading.Thread(target=client.receive_messages, args=(20,))
    recv_thread.daemon = True
    recv_thread.start()

    # 发送测试消息
    for i in range(1, num_messages + 1):
        message = f"测试消息 {i} - 时间: {time.strftime('%H:%M:%S')}"
        client.send_message(message)
        time.sleep(2)  # 间隔2秒

    print(f"已发送 {num_messages} 条测试消息")
    time.sleep(5)  # 等待接收可能的回复






def start_p2p():
    client_name = b"n4n4n4"
    server_host = 'jifen.mp-wexin.work'
    server_port = 1721
    src_port_start = 30000
    count = 25
    offset= 20
    check_peer = None
    while True:
        try:
            n4c = N4Client(
                ident=my_name,
                server_host=server_host,
                server_port=server_port,
                src_port_start=src_port_start,
                src_port_count=count,
                peer_port_offset=offset,
                allow_cross_ip=check_peer
            )
            logging.info("==================")
            logging.info("Source port: %d-%d" % (src_port_start, src_port_start+count))
            peer, src_port = n4c.punch(wait=10)
            peer_ip, peer_port = peer
            logging.info("------")
            logging.info("Local port:    %d" % src_port)
            logging.info("Peer address:  %s:%d" % (peer_ip, peer_port))
            logging.info("------")
            logging.info("[ WIN ]")
            logging.info("------")
            logging.info("> nc -u -p %d %s %d" % (src_port, peer_ip, peer_port))
            return src_port, peer_port, peer_ip
            return P2pClient(peer_port, peer_ip, local_src_port, None, None)
            break
        except N4Error.PunchFailurelocal_src_port:
            logging.info("[ LOSE ]")
            src_port_start += count
            continue

def main():
    src_port, peer_port, peer_ip = start_p2p()
    client = P2pClient(src_port, peer_ip, peer_port)
    print("2. 自动测试模式（自动发送测试消息）")
    # if choice == "1":
    interactive_mode(client)
    # elif choice == "2":
    #     auto_test_mode(client, num_messages=5)

if __name__ == '__main__':
    main()