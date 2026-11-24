import html
from security import KEY_RE

LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PawDrop · Sign in</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:sans-serif;background:#f4f4f4;display:flex;align-items:center;justify-content:center;min-height:100vh}
.box{background:#fff;padding:32px;border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,.12);width:100%;max-width:360px}
h1{font-size:1.2rem;margin-bottom:20px;color:#333}
input{width:100%;padding:10px 12px;border:1px solid #ccc;border-radius:4px;font-size:1rem;margin-bottom:14px}
button{width:100%;padding:10px;background:#b45309;color:#fff;border:none;border-radius:4px;font-size:1rem;cursor:pointer}
button:hover{background:#92400e}
.err{color:#dc2626;font-size:.9rem;margin-bottom:10px}
</style>
</head>
<body>
<div class="box">
  <h1>PawDrop · Sign in</h1>
  {error}
  <form method="post" action="/admin/login">
    <input type="password" name="password" autocomplete="current-password" required placeholder="Password" autofocus>
    <button type="submit">Sign in</button>
  </form>
</div>
</body>
</html>"""

ADMIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PawDrop · Files</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:sans-serif;background:#f4f4f4;padding:20px}
.wrap{max-width:700px;margin:0 auto}
h1{font-size:1.3rem;margin-bottom:16px;color:#333}
.toolbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.btn{padding:8px 16px;border:none;border-radius:4px;cursor:pointer;font-size:.9rem;text-decoration:none;display:inline-block}
.btn-add{background:#b45309;color:#fff}
.btn-add:hover{background:#92400e}
.btn-del{background:#dc2626;color:#fff}
.btn-del:hover{background:#b91c1c}
.btn-get{background:#059669;color:#fff}
.btn-get:hover{background:#047857}
.btn-out{background:#6b7280;color:#fff}
.btn-out:hover{background:#4b5563}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:6px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.08)}
th,td{padding:11px 14px;text-align:left;border-bottom:1px solid #e5e7eb;font-size:.9rem}
th{background:#f9fafb;font-weight:600;color:#374151}
td:last-child{white-space:nowrap}
.uuid{color:#6b7280;font-size:.8rem;word-break:break-all}
.empty{text-align:center;padding:30px;color:#9ca3af}
.modal-bg{display:none;position:fixed;inset:0;background:rgba(0,0,0,.4);align-items:center;justify-content:center;z-index:100}
.modal-bg.open{display:flex}
.modal{background:#fff;padding:28px;border-radius:6px;width:100%;max-width:420px;box-shadow:0 4px 20px rgba(0,0,0,.2)}
.modal h2{font-size:1.1rem;margin-bottom:16px}
.modal input,.modal label{display:block;width:100%;margin-bottom:12px}
.modal input[type=text],.modal input[type=file]{padding:9px 11px;border:1px solid #ccc;border-radius:4px;font-size:.9rem}
.modal-foot{display:flex;gap:10px;justify-content:flex-end;margin-top:6px}
.btn-cancel{background:#e5e7eb;color:#374151}
.btn-cancel:hover{background:#d1d5db}
.link{color:#2563eb;font-size:.8rem}
</style>
</head>
<body>
<div class="wrap">
  <div class="toolbar">
    <h1>PawDrop</h1>
    <div style="display:flex;gap:8px">
      <button class="btn btn-add" onclick="openModal()">+ Add file</button>
      <form method="post" action="/admin/logout" style="margin:0">
        <input type="hidden" name="csrf" value="{csrf}">
        <button type="submit" class="btn btn-out">Sign out</button>
      </form>
    </div>
  </div>

  <table>
    <thead><tr><th>Filename</th><th>Key / link</th><th></th></tr></thead>
    <tbody>
    {rows}
    </tbody>
  </table>
</div>

<div class="modal-bg" id="modal">
  <div class="modal">
    <h2>Add file</h2>
    <form method="post" action="/admin/upload" enctype="multipart/form-data">
      <input type="hidden" name="csrf" value="{csrf}">
      <input type="text" name="uuid" placeholder="Random key (optional)" minlength="22" maxlength="128">
      <input type="file" name="file" accept=".txt" required>
      <div class="modal-foot">
        <button type="button" class="btn btn-cancel" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn btn-add">Upload</button>
      </div>
    </form>
  </div>
</div>

<script>
function openModal(){document.getElementById('modal').classList.add('open')}
function closeModal(){document.getElementById('modal').classList.remove('open')}
document.getElementById('modal').addEventListener('click',function(e){if(e.target===this)closeModal()})
</script>
</body>
</html>"""


def render_login(error_message: str = "") -> str:
    error_html = f"<p class='err'>{html.escape(error_message, quote=True)}</p>" if error_message else ""
    return LOGIN_HTML.replace("{error}", error_html)


def render_admin(rows: str, csrf: str) -> str:
    return ADMIN_HTML.replace("{csrf}", html.escape(csrf, quote=True)).replace("{rows}", rows)


def render_admin_rows(meta: dict, base_url: str, csrf: str) -> str:
    rows = ""
    safe_csrf = html.escape(csrf, quote=True)
    for uuid, info in meta.items():
        if not KEY_RE.fullmatch(uuid):
            continue
        filename = str(info.get("filename") or "—")
        link = f"{base_url}/{uuid}" if base_url else f"/{uuid}"

        safe_uuid = html.escape(uuid, quote=True)
        safe_fname = html.escape(filename, quote=True)
        safe_link = html.escape(link, quote=True)

        rows += (
            f"<tr>"
            f"<td>{safe_fname}</td>"
            f"<td><span class='uuid'>{safe_uuid}</span><br>"
            f"<a class='link' href='{safe_link}' target='_blank' rel='noopener noreferrer'>{safe_link}</a></td>"
            f"<td>"
            f"<a class='btn btn-get' href='/admin/download/{safe_uuid}' download>Download</a> "
            f"<form method='post' action='/admin/delete' style='margin:0'>"
            f"<input type='hidden' name='uuid' value='{safe_uuid}'>"
            f"<input type='hidden' name='csrf' value='{safe_csrf}'>"
            f"<button type='submit' class='btn btn-del'>Delete</button>"
            f"</form></td>"
            f"</tr>"
        )

    if not rows:
        rows = "<tr><td colspan='3' class='empty'>No files. The cat is waiting.</td></tr>"
    return rows

