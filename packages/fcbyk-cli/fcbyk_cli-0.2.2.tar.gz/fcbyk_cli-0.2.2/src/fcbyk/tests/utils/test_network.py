"""测试网络工具函数"""

import socket
from types import SimpleNamespace
from unittest.mock import patch

from fcbyk.utils.network import detect_iface_type, get_private_networks


def _addr(family, address):
    """创建一个模拟的 psutil 地址对象，只包含测试所需字段。"""
    return SimpleNamespace(family=family, address=address)


def test_detect_iface_type():
    """测试 detect_iface_type() 能否根据关键字正确识别网卡类型。"""
    # 虚拟网卡
    assert detect_iface_type("vboxnet0") == ("virtualbox", True, 30)
    assert detect_iface_type("VMware Network Adapter VMnet8") == ("vmware", True, 30)
    assert detect_iface_type("WSL") == ("container", True, 40)

    # 物理网卡
    assert detect_iface_type("以太网") == ("ethernet", False, 10)
    assert detect_iface_type("Wi-Fi") == ("wifi", False, 10)

    # 未知网卡
    assert detect_iface_type("unknown123") == ("unknown", False, 50)


def test_get_private_networks_loopback_logic():
    """测试 get_private_networks() 对回环地址的处理逻辑。"""
    # 注意：get_private_networks 只收集私有网段（10./192.168./172.），
    # 127.* 不会被加入最终列表，除非没有其他网络
    mock_addrs = {
        "loopback": [
            _addr(socket.AF_INET, "127.0.0.1"),
        ]
    }

    with patch("psutil.net_if_addrs", return_value=mock_addrs):
        # 当没有可用网络时，会返回包含回环地址的列表
        result = get_private_networks()
        
        # 应该返回包含回环地址的列表，因为没有其他网络
        assert len(result) == 1
        assert result[0]["iface"] == "localhost"
        assert result[0]["ips"] == ["127.0.0.1"]
        assert result[0]["type"] == "loopback"


def test_get_private_networks_filters_and_sorts():
    """测试 get_private_networks() 能否正确过滤、识别并排序网卡。"""
    mock_addrs = {
        # 名称需包含关键字才能命中规则
        "Ethernet": [
            _addr(socket.AF_INET, "192.168.1.100"),
            _addr(socket.AF_INET6, "fe80::1"),  # 应被过滤
        ],
        "WLAN": [
            _addr(socket.AF_INET, "10.0.0.2"),
        ],
        "apipa0": [
            _addr(socket.AF_INET, "169.254.1.1"),  # APIPA 地址应被过滤
        ],
    }

    with patch("psutil.net_if_addrs", return_value=mock_addrs):
        result = get_private_networks()
        assert len(result) == 2

        # 按 a-z 排序，Ethernet 在前
        assert result[0]["iface"] == "Ethernet"
        assert result[0]["type"] == "ethernet"
        assert not result[0]["virtual"]
        assert "192.168.1.100" in result[0]["ips"]

        assert result[1]["iface"] == "WLAN"
        assert result[1]["type"] == "wifi"
        assert "10.0.0.2" in result[1]["ips"]


def test_get_private_networks_no_valid_ips():
    """测试当 psutil 返回的网卡不含有效 IP 时，结果为包含回环地址的列表。"""
    with patch("psutil.net_if_addrs", return_value={"Ethernet": []}):
        result = get_private_networks()
        assert len(result) == 1
        assert result[0]["iface"] == "localhost"
        assert result[0]["ips"] == ["127.0.0.1"]
        assert result[0]["type"] == "loopback"


def test_get_private_networks_skips_non_ipv4():
    """测试 get_private_networks() 会跳过非 IPv4 地址。"""
    mock_addrs = {
        "Ethernet": [
            _addr(socket.AF_INET6, "fe80::1"),
        ]
    }

    with patch("psutil.net_if_addrs", return_value=mock_addrs):
        result = get_private_networks()
        # 当只有 IPv6 地址时，会返回包含回环地址的列表
        assert len(result) == 1
        assert result[0]["iface"] == "localhost"
        assert result[0]["ips"] == ["127.0.0.1"]
        assert result[0]["type"] == "loopback"
