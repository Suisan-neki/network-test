# network-test

Raspberry Pi 上で動かす、ネットワーク観測ダッシュボード（Flask）の MVP 実装です。

## 構成

```text
observer/
 ├ app.py
 ├ config.py
 ├ config.yaml
 ├ collectors/
 ├ templates/
 ├ static/
 └ systemd/
```

## セットアップ

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 起動

```bash
python3 -m observer.app
```

デフォルトは `0.0.0.0:5000` で待ち受けます。

`DHCP_LEASE_FILE` は既定で `auto` です。以下を順に探して読み取ります。

- `/var/lib/dhcp/dhcpd.leases` (isc-dhcp-server)
- `/var/lib/misc/dnsmasq.leases` (dnsmasq)

## API

- `GET /api/status`
- `GET /api/dhcp_leases`
- `GET /api/logs`

## テスト

```bash
pytest -q
```

## systemd

`observer/systemd/observer.service` は Raspberry Pi を想定して以下を既定にしています。

- `User=pi`
- `WorkingDirectory=/home/pi/network-test`
- `OBSERVER_CONFIG=/home/pi/network-test/observer/config.yaml`

必要に応じてパスだけ調整してください。
