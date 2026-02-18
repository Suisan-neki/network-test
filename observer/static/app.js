async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`${url}: ${response.status}`);
  }
  return response.json();
}

function asText(value, fallback = "-") {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}

function renderSummary(status) {
  const root = document.getElementById("summary");
  const wan = status.interfaces?.wan || {};
  const lan = status.interfaces?.lan || {};
  const nat = status.nat || {};
  const pingIp = status.connectivity?.ip || {};
  const pingDns = status.connectivity?.dns || {};
  const route = status.default_route || {};

  const cards = [
    ["WAN IP", asText(wan.ip)],
    ["WAN State", asText(wan.state)],
    ["LAN IP", asText(lan.ip)],
    ["LAN State", asText(lan.state)],
    ["Default Route", asText(route.via || route.dev)],
    ["NAT", nat.enabled ? "Enabled" : "Disabled"],
    ["Ping IP", pingIp.ok ? `OK ${asText(pingIp.rtt_ms)} ms` : "NG"],
    ["Ping DNS", pingDns.ok ? `OK ${asText(pingDns.rtt_ms)} ms` : "NG"],
  ];

  root.innerHTML = cards
    .map(([label, value]) => {
      const cls = /^(Enabled|OK)/.test(value) ? "ok" : /^(Disabled|NG)/.test(value) ? "bad" : "";
      return `<div class="summary-card"><div class="label">${label}</div><div class="value ${cls}">${value}</div></div>`;
    })
    .join("");
}

function renderDhcp(leases) {
  const body = document.getElementById("dhcp-body");
  if (!Array.isArray(leases) || leases.length === 0) {
    body.innerHTML = `<tr><td colspan="5">No leases</td></tr>`;
    return;
  }

  body.innerHTML = leases
    .map(
      (lease) => `
      <tr>
        <td>${asText(lease.ip)}</td>
        <td>${asText(lease.mac)}</td>
        <td>${asText(lease.hostname)}</td>
        <td>${asText(lease.state)}</td>
        <td>${asText(lease.last_seen)}</td>
      </tr>`
    )
    .join("");
}

function renderLogs(logs) {
  const root = document.getElementById("logs");
  if (!Array.isArray(logs) || logs.length === 0) {
    root.innerHTML = `<div class="log-line">No logs</div>`;
    return;
  }

  root.innerHTML = logs
    .slice(-120)
    .reverse()
    .map(
      (item) =>
        `<div class="log-line">[${asText(item.ts)}] <span class="type">${asText(item.type)}</span>${asText(item.source)}: ${asText(item.msg)}</div>`
    )
    .join("");
}

async function refreshAll() {
  try {
    const [status, dhcp, logs] = await Promise.all([
      fetchJson("/api/status"),
      fetchJson("/api/dhcp_leases"),
      fetchJson("/api/logs"),
    ]);
    renderSummary(status);
    renderDhcp(dhcp);
    renderLogs(logs);
  } catch (err) {
    console.error(err);
  }
}

const refreshSec = Number(document.body.dataset.refresh || "5");
refreshAll();
setInterval(refreshAll, Math.max(1, refreshSec) * 1000);

