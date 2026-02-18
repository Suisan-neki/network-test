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

## API

- `GET /api/status`
- `GET /api/dhcp_leases`
- `GET /api/logs`

## テスト

```bash
pytest -q
```

## systemd

`observer/systemd/observer.service` をベースに `WorkingDirectory` / `ExecStart` / `User` を環境に合わせて調整してください。
