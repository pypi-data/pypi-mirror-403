from typing_extensions import TypedDict


class RuleEntity(TypedDict):
    # {
    #     "name": "xjy_test",
    #     "source_client": "家里小主机",
    #     "target_client": "xinjiaya_server_test",
    #     "local_port": 33333,
    #     "local_ip": "127.0.0.1",
    #     "protocol": "tcp",
    #     "speed_limit": 0.0,
    #     "enabled": true,
    #     "p2p_enabled": false,
    #     "target_ip": "127.0.0.1",
    #     "target_port": 22
    # }
    name: str
    source_client: str
    target_client: str
    local_port: int
    local_ip: str
    protocol: str
    speed_limit: float
    enabled: bool
    p2p_enabled: bool
    target_ip: str
    target_port: int
