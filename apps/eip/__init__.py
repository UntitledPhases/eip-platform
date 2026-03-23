"""EIP Wake — Flask Blueprint. Wake-on-LAN and hub status monitoring."""

from flask import Blueprint, render_template_string, jsonify
from datetime import datetime, timezone
import subprocess
import os

bp = Blueprint("eip", __name__)

CMD = ["wakepc", "hub"]
HUB_IP = os.environ.get("EIP_HUB_IP", "192.168.4.40")
HUB_PORT = int(os.environ.get("EIP_HUB_PORT", "3389"))
NC_TIMEOUT = int(os.environ.get("EIP_NC_TIMEOUT", "2"))

_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>EIP Wake</title></head>
<body style="background:#111;color:#e0e0e0;font-family:sans-serif;padding:2rem;">
  <h1>EIP Wake</h1>
  {% if output %}<pre style="background:#222;padding:1rem;border-radius:6px;">{{ output }}</pre>{% endif %}
  <form method="post" action="{{ url_for('eip.wake') }}">
    <button type="submit" style="padding:0.5rem 1.5rem;font-size:1rem;cursor:pointer;">Wake Hub</button>
  </form>
</body>
</html>
"""

@bp.get("/api/status/hub")
def hub_status():
    ts = datetime.now(timezone.utc).isoformat()
    try:
        r = subprocess.run(["nc", "-z", HUB_IP, str(HUB_PORT)], capture_output=True, text=True, timeout=NC_TIMEOUT, check=False)
        status = "ONLINE" if r.returncode == 0 else "OFFLINE"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        status = "OFFLINE"
    return jsonify({"status": status, "timestamp": ts})

@bp.get("/")
def index():
    return render_template_string(_TEMPLATE, output=None)

@bp.post("/wake")
def wake():
    try:
        result = subprocess.run(CMD, capture_output=True, text=True, timeout=10)
        output = (result.stdout or "") + (result.stderr or "")
        output = output.strip() or f"Exit code {result.returncode} (no output)"
    except Exception as e:
        output = str(e)
    return render_template_string(_TEMPLATE, output=output)
