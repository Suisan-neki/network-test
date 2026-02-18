from observer.collectors.command import CommandResult
from observer.collectors.dhcp import parse_dhcp_leases
from observer.collectors.interfaces import collect_interface_status, parse_default_route
from observer.collectors.nat import parse_nat_postrouting


def test_parse_nat_postrouting_enabled():
    output = """
    -N POSTROUTING
    -A POSTROUTING -o wlan0 -j MASQUERADE
    """
    enabled, rule = parse_nat_postrouting(output)
    assert enabled is True
    assert "MASQUERADE" in rule


def test_parse_nat_postrouting_disabled():
    output = "-N POSTROUTING\n-A POSTROUTING -o wlan0 -j ACCEPT\n"
    enabled, rule = parse_nat_postrouting(output)
    assert enabled is False
    assert rule == ""


def test_parse_default_route():
    route = parse_default_route(
        "default via 192.168.1.1 dev wlan0 proto dhcp src 192.168.1.50 metric 303\n"
    )
    assert route["via"] == "192.168.1.1"
    assert route["dev"] == "wlan0"


def test_parse_dhcp_leases_extract_latest():
    content = """
    lease 192.168.50.10 {
      starts 3 2026/02/18 11:58:00;
      ends 3 2026/02/18 12:58:00;
      binding state active;
      hardware ethernet aa:bb:cc:dd:ee:01;
      client-hostname "sensor-node";
    }
    lease 192.168.50.10 {
      starts 3 2026/02/18 10:00:00;
      ends 3 2026/02/18 11:00:00;
      binding state free;
      hardware ethernet aa:bb:cc:dd:ee:ff;
      client-hostname "old-node";
    }
    """
    leases = parse_dhcp_leases(content)
    assert len(leases) == 1
    assert leases[0]["hostname"] == "sensor-node"
    assert leases[0]["state"] == "active"
    assert leases[0]["ip"] == "192.168.50.10"


def test_collect_interface_status_no_crash_on_command_error():
    def failing_runner(_cmd, _timeout=3):
        return CommandResult(stdout="", stderr="failed", returncode=1)

    result = collect_interface_status("wlan0", "eth0", command_runner=failing_runner)
    assert result["interfaces"]["wan"]["name"] == "wlan0"
    assert result["interfaces"]["lan"]["name"] == "eth0"
    assert result["default_route"] == {}
    assert result["errors"]

