import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Tuple


def _config_dir() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    return base / "pactown" / "pactowncom"


def _token_path() -> Path:
    return _config_dir() / "admin_token"


def _user_cookie_path() -> Path:
    return _config_dir() / "user_access_token"


def _load_saved_admin_token() -> Optional[str]:
    p = _token_path()
    if not p.exists():
        return None
    try:
        return p.read_text(encoding="utf-8").strip() or None
    except Exception:
        return None


def _save_admin_token(token: str) -> None:
    d = _config_dir()
    d.mkdir(parents=True, exist_ok=True)
    p = _token_path()
    p.write_text(str(token).strip() + "\n", encoding="utf-8")
    try:
        os.chmod(p, 0o600)
    except Exception:
        pass


def _load_saved_user_access_token() -> Optional[str]:
    p = _user_cookie_path()
    if not p.exists():
        return None
    try:
        return p.read_text(encoding="utf-8").strip() or None
    except Exception:
        return None


def _save_user_access_token(token: str) -> None:
    d = _config_dir()
    d.mkdir(parents=True, exist_ok=True)
    p = _user_cookie_path()
    p.write_text(str(token).strip() + "\n", encoding="utf-8")
    try:
        os.chmod(p, 0o600)
    except Exception:
        pass


def _delete_saved_user_access_token() -> None:
    try:
        _user_cookie_path().unlink(missing_ok=True)  # type: ignore[arg-type]
    except TypeError:
        try:
            p = _user_cookie_path()
            if p.exists():
                p.unlink()
        except Exception:
            pass
    except Exception:
        pass


def _curl_available() -> bool:
    return bool(shutil.which("curl"))


def _run_curl(args: Sequence[str], *, stream: bool = False) -> int:
    if not _curl_available():
        raise RuntimeError("curl not found in PATH")
    p = subprocess.Popen(list(args)) if stream else subprocess.run(list(args))
    if stream:
        return int(p.wait())
    return int(getattr(p, "returncode", 0) or 0)


def _json_pretty_print(data: bytes) -> None:
    try:
        obj = json.loads(data.decode("utf-8"))
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    except Exception:
        sys.stdout.buffer.write(data)
        if not data.endswith(b"\n"):
            sys.stdout.write("\n")


def _http_call(*, base_url: str, path: str, method: str, bearer: Optional[str], cookie: Optional[str],
              json_body: Optional[str], json_file: Optional[str], stream: bool, out: Optional[str]) -> int:
    url = base_url.rstrip("/") + path

    cmd = ["curl", "-sS", "-X", method.upper()]
    if stream:
        cmd.insert(1, "-N")
    if bearer:
        cmd.extend(["-H", f"Authorization: Bearer {bearer}"])
    if cookie:
        cmd.extend(["-H", f"Cookie: {cookie}"])

    body_added = False
    if json_file:
        cmd.extend(["-H", "Content-Type: application/json", "--data-binary", f"@{json_file}"])
        body_added = True
    elif json_body is not None:
        cmd.extend(["-H", "Content-Type: application/json", "--data-raw", json_body])
        body_added = True

    if method.upper() == "GET" and body_added:
        pass

    if out:
        cmd.extend(["-o", out])

    cmd.append(url)

    if stream or out:
        return _run_curl(cmd, stream=True)

    proc = subprocess.run(cmd, capture_output=True)
    if proc.stdout:
        _json_pretty_print(proc.stdout)
    if proc.stderr:
        sys.stderr.write(proc.stderr.decode("utf-8", errors="ignore"))
    return int(proc.returncode or 0)


def _http_call_capture_status(
    *,
    base_url: str,
    path: str,
    method: str,
    bearer: Optional[str],
    cookie: Optional[str],
    json_body: Optional[str],
    json_file: Optional[str],
) -> Tuple[Optional[int], bytes, bytes]:
    url = base_url.rstrip("/") + path
    marker = "__HTTP_STATUS__"

    cmd = ["curl", "-sS", "-X", method.upper()]
    if bearer:
        cmd.extend(["-H", f"Authorization: Bearer {bearer}"])
    if cookie:
        cmd.extend(["-H", f"Cookie: {cookie}"])

    if json_file:
        cmd.extend(["-H", "Content-Type: application/json", "--data-binary", f"@{json_file}"])
    elif json_body is not None:
        cmd.extend(["-H", "Content-Type: application/json", "--data-raw", json_body])

    cmd.extend(["-w", f"\n{marker}:%{{http_code}}"])
    cmd.append(url)

    proc = subprocess.run(cmd, capture_output=True)
    out = proc.stdout or b""
    err = proc.stderr or b""

    status: Optional[int] = None
    needle = ("\n" + marker + ":").encode("utf-8")
    if needle in out:
        body, status_part = out.rsplit(needle, 1)
        try:
            status = int(status_part.decode("utf-8", errors="ignore").strip()[:3])
        except Exception:
            status = None
        out = body

    return status, out, err


def _default_base_url() -> str:
    return os.environ.get("PACTOWNCOM_API_BASE_URL") or os.environ.get("API_BASE_URL") or "http://localhost:8001"


def _admin_env_credentials() -> Tuple[str, str]:
    username = str(
        os.environ.get("PACTOWNCOM_ADMIN_USERNAME")
        or os.environ.get("ADMIN_USERNAME")
        or os.environ.get("ADMIN_DEFAULT_USERNAME")
        or "admin"
    ).strip()
    password = str(
        os.environ.get("PACTOWNCOM_ADMIN_PASSWORD")
        or os.environ.get("ADMIN_PASSWORD")
        or os.environ.get("ADMIN_DEFAULT_PASSWORD")
        or ""
    )
    return username, password


def _admin_login_and_get_token(*, base_url: str, username: str, password: str) -> str:
    body = json.dumps({"username": username, "password": password})
    status, out, err = _http_call_capture_status(
        base_url=base_url,
        path="/admin/login",
        method="POST",
        bearer=None,
        cookie=None,
        json_body=body,
        json_file=None,
    )
    if err:
        sys.stderr.write(err.decode("utf-8", errors="ignore"))
    if status is not None and status >= 400:
        _json_pretty_print(out)
        raise SystemExit(f"Admin login failed (status={status})")

    try:
        data = json.loads(out.decode("utf-8"))
    except Exception:
        sys.stdout.buffer.write(out)
        raise SystemExit("Admin login failed: unexpected response")

    token = str((data or {}).get("token") or "").strip()
    if not token:
        raise SystemExit("Admin login failed: missing token in response")
    return token


def _get_or_login_admin_token(*, base_url: str, token_arg: Optional[str]) -> str:
    token = str(
        (token_arg or "").strip()
        or (os.environ.get("PACTOWNCOM_ADMIN_TOKEN") or "").strip()
        or (os.environ.get("ADMIN_TOKEN") or "").strip()
        or (_load_saved_admin_token() or "").strip()
    )
    if token:
        return token

    username, password = _admin_env_credentials()
    if not password:
        raise SystemExit(
            "Missing admin token. Set ADMIN_TOKEN/PACTOWNCOM_ADMIN_TOKEN, "
            "or set PACTOWNCOM_ADMIN_PASSWORD (and optionally PACTOWNCOM_ADMIN_USERNAME) "
            "to enable auto-login, or run: pactowncom admin login --save --password '...'."
        )

    token = _admin_login_and_get_token(base_url=base_url, username=username, password=password)
    _save_admin_token(token)
    return token


def _get_user_access_cookie(*, token_arg: Optional[str]) -> str:
    token = str(
        (token_arg or "").strip()
        or (os.environ.get("PACTOWNCOM_ACCESS_TOKEN") or "").strip()
        or (os.environ.get("ACCESS_TOKEN") or "").strip()
        or (_load_saved_user_access_token() or "").strip()
    )
    if not token:
        raise SystemExit(
            "Missing user access token cookie. "
            "Use: pactowncom user set-access-token --access-token '...' (copy cookie value 'access_token' from browser), "
            "or set PACTOWNCOM_ACCESS_TOKEN/ACCESS_TOKEN env."
        )
    return f"access_token={token}"


def cmd_admin_login(args: argparse.Namespace) -> int:
    base_url = str(args.base_url or _default_base_url())
    env_user, env_pass = _admin_env_credentials()
    username = str(args.username or env_user)
    password = str(args.password or env_pass)
    if not password:
        raise SystemExit(
            "Missing password. Provide --password, or set PACTOWNCOM_ADMIN_PASSWORD/ADMIN_PASSWORD env."
        )

    token = _admin_login_and_get_token(base_url=base_url, username=username, password=password)
    if args.save:
        _save_admin_token(token)
    print(json.dumps({"token": token}, ensure_ascii=False, indent=2))
    return 0


def cmd_admin_call(args: argparse.Namespace) -> int:
    base_url = str(args.base_url or _default_base_url())
    token = _get_or_login_admin_token(base_url=base_url, token_arg=args.token)

    if bool(args.stream) or args.out:
        return _http_call(
            base_url=base_url,
            path=str(args.path),
            method=str(args.method or "GET"),
            bearer=token,
            cookie=None,
            json_body=args.json,
            json_file=args.json_file,
            stream=bool(args.stream),
            out=args.out,
        )

    status, out, err = _http_call_capture_status(
        base_url=base_url,
        path=str(args.path),
        method=str(args.method or "GET"),
        bearer=token,
        cookie=None,
        json_body=args.json,
        json_file=args.json_file,
    )
    if status == 401:
        username, password = _admin_env_credentials()
        if password:
            token = _admin_login_and_get_token(base_url=base_url, username=username, password=password)
            _save_admin_token(token)
            status, out, err = _http_call_capture_status(
                base_url=base_url,
                path=str(args.path),
                method=str(args.method or "GET"),
                bearer=token,
                cookie=None,
                json_body=args.json,
                json_file=args.json_file,
            )
    if err:
        sys.stderr.write(err.decode("utf-8", errors="ignore"))
    if status is not None and status >= 400:
        _json_pretty_print(out)
        return 1
    if out:
        _json_pretty_print(out)
    return 0


def cmd_api_call(args: argparse.Namespace) -> int:
    base_url = str(args.base_url or _default_base_url())
    bearer = args.bearer
    cookie = args.cookie
    return _http_call(
        base_url=base_url,
        path=str(args.path),
        method=str(args.method or "GET"),
        bearer=bearer,
        cookie=cookie,
        json_body=args.json,
        json_file=args.json_file,
        stream=bool(args.stream),
        out=args.out,
    )


def cmd_admin_shortcut(args: argparse.Namespace) -> int:
    base_url = str(args.base_url or _default_base_url())
    token = _get_or_login_admin_token(base_url=base_url, token_arg=args.token)

    if args.action == "startup-restore-logs":
        path = f"/admin/system-events?event_type=startup_restore&limit={int(args.limit or 80)}"
        status, out, err = _http_call_capture_status(
            base_url=base_url,
            path=path,
            method="GET",
            bearer=token,
            cookie=None,
            json_body=None,
            json_file=None,
        )
        if status == 401:
            username, password = _admin_env_credentials()
            if password:
                token = _admin_login_and_get_token(base_url=base_url, username=username, password=password)
                _save_admin_token(token)
                status, out, err = _http_call_capture_status(
                    base_url=base_url,
                    path=path,
                    method="GET",
                    bearer=token,
                    cookie=None,
                    json_body=None,
                    json_file=None,
                )
        if err:
            sys.stderr.write(err.decode("utf-8", errors="ignore"))
        if status is not None and status >= 400:
            _json_pretty_print(out)
            return 1
        _json_pretty_print(out)
        return 0

    if args.action == "all-autostart":
        path = "/admin/user-storages/autostart-runner-projects"
        status, out, err = _http_call_capture_status(
            base_url=base_url,
            path=path,
            method="GET",
            bearer=token,
            cookie=None,
            json_body=None,
            json_file=None,
        )
        if status == 401:
            username, password = _admin_env_credentials()
            if password:
                token = _admin_login_and_get_token(base_url=base_url, username=username, password=password)
                _save_admin_token(token)
                status, out, err = _http_call_capture_status(
                    base_url=base_url,
                    path=path,
                    method="GET",
                    bearer=token,
                    cookie=None,
                    json_body=None,
                    json_file=None,
                )
        if err:
            sys.stderr.write(err.decode("utf-8", errors="ignore"))
        if status is not None and status >= 400:
            _json_pretty_print(out)
            return 1
        _json_pretty_print(out)
        return 0

    if args.action == "user-autostart":
        if not args.username:
            raise SystemExit("Missing --username")
        path = f"/admin/user-storages/{args.username}/autostart-runner-projects"
        status, out, err = _http_call_capture_status(
            base_url=base_url,
            path=path,
            method="GET",
            bearer=token,
            cookie=None,
            json_body=None,
            json_file=None,
        )
        if status == 401:
            username, password = _admin_env_credentials()
            if password:
                token = _admin_login_and_get_token(base_url=base_url, username=username, password=password)
                _save_admin_token(token)
                status, out, err = _http_call_capture_status(
                    base_url=base_url,
                    path=path,
                    method="GET",
                    bearer=token,
                    cookie=None,
                    json_body=None,
                    json_file=None,
                )
        if err:
            sys.stderr.write(err.decode("utf-8", errors="ignore"))
        if status is not None and status >= 400:
            _json_pretty_print(out)
            return 1
        _json_pretty_print(out)
        return 0

    raise SystemExit("Unknown action")


def cmd_user_set_access_token(args: argparse.Namespace) -> int:
    token = str(args.access_token or "").strip()
    if not token:
        raise SystemExit("Missing --access-token")
    _save_user_access_token(token)
    print(json.dumps({"saved": True, "path": str(_user_cookie_path())}, ensure_ascii=False, indent=2))
    return 0


def cmd_user_call(args: argparse.Namespace) -> int:
    base_url = str(args.base_url or _default_base_url())
    cookie = _get_user_access_cookie(token_arg=args.access_token)

    if bool(args.stream) or args.out:
        return _http_call(
            base_url=base_url,
            path=str(args.path),
            method=str(args.method or "GET"),
            bearer=None,
            cookie=cookie,
            json_body=args.json,
            json_file=args.json_file,
            stream=bool(args.stream),
            out=args.out,
        )

    status, out, err = _http_call_capture_status(
        base_url=base_url,
        path=str(args.path),
        method=str(args.method or "GET"),
        bearer=None,
        cookie=cookie,
        json_body=args.json,
        json_file=args.json_file,
    )
    if err:
        sys.stderr.write(err.decode("utf-8", errors="ignore"))
    if status == 401:
        raise SystemExit(
            "Unauthorized (401). Your saved cookie is missing/expired. "
            "Log in via browser again and run: pactowncom user set-access-token --access-token '...'."
        )
    if status is not None and status >= 400:
        _json_pretty_print(out)
        return 1
    if out:
        _json_pretty_print(out)
    return 0


def cmd_user_logout(args: argparse.Namespace) -> int:
    base_url = str(args.base_url or _default_base_url())
    cookie = None
    try:
        cookie = _get_user_access_cookie(token_arg=args.access_token)
    except Exception:
        cookie = None

    if cookie:
        _http_call(
            base_url=base_url,
            path="/auth/logout",
            method="POST",
            bearer=None,
            cookie=cookie,
            json_body=None,
            json_file=None,
            stream=False,
            out=None,
        )

    _delete_saved_user_access_token()
    print(json.dumps({"ok": True, "cleared": True}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pactowncom")
    p.add_argument("--base-url", default=None, help="API base URL (default: http://localhost:8001)")

    sub = p.add_subparsers(dest="cmd", required=True)

    api = sub.add_parser("api", help="Call arbitrary API endpoint")
    api.add_argument("--path", required=True, help="Path like /health")
    api.add_argument("--method", default="GET")
    api.add_argument("--bearer", default=None)
    api.add_argument("--cookie", default=None, help="Raw Cookie header value (e.g. access_token=...)")
    api.add_argument("--json", default=None)
    api.add_argument("--json-file", default=None)
    api.add_argument("--stream", action="store_true")
    api.add_argument("--out", default=None)
    api.set_defaults(func=cmd_api_call)

    admin = sub.add_parser("admin", help="Admin operations")
    admin_sub = admin.add_subparsers(dest="admin_cmd", required=True)

    login = admin_sub.add_parser("login", help="Login and print admin token")
    login.add_argument("--username", default=None)
    login.add_argument("--password", default=None)
    login.add_argument("--save", action="store_true", help="Save token to ~/.config/pactown/pactowncom/admin_token")
    login.set_defaults(func=cmd_admin_login)

    call = admin_sub.add_parser("call", help="Call arbitrary /admin endpoint")
    call.add_argument("--token", default=None)
    call.add_argument("--path", required=True, help="Path like /admin/me")
    call.add_argument("--method", default="GET")
    call.add_argument("--json", default=None)
    call.add_argument("--json-file", default=None)
    call.add_argument("--stream", action="store_true")
    call.add_argument("--out", default=None)
    call.set_defaults(func=cmd_admin_call)

    short = admin_sub.add_parser("do", help="Shortcuts")
    short.add_argument("action", choices=["startup-restore-logs", "all-autostart", "user-autostart"])
    short.add_argument("--token", default=None)
    short.add_argument("--username", default=None)
    short.add_argument("--limit", default=80)
    short.set_defaults(func=cmd_admin_shortcut)

    user = sub.add_parser("user", help="User operations (uses access_token cookie)")
    user_sub = user.add_subparsers(dest="user_cmd", required=True)

    set_tok = user_sub.add_parser("set-access-token", help="Save access_token cookie value for future commands")
    set_tok.add_argument("--access-token", required=True, help="Cookie value (not the full 'access_token=...')")
    set_tok.set_defaults(func=cmd_user_set_access_token)

    user_call = user_sub.add_parser("call", help="Call arbitrary endpoint as a user (cookie auth)")
    user_call.add_argument("--access-token", default=None, help="Override saved token (cookie value)")
    user_call.add_argument("--path", required=True, help="Path like /users/me/services")
    user_call.add_argument("--method", default="GET")
    user_call.add_argument("--json", default=None)
    user_call.add_argument("--json-file", default=None)
    user_call.add_argument("--stream", action="store_true")
    user_call.add_argument("--out", default=None)
    user_call.set_defaults(func=cmd_user_call)

    user_logout = user_sub.add_parser("logout", help="Call /auth/logout and clear saved cookie")
    user_logout.add_argument("--access-token", default=None, help="Override saved token (cookie value)")
    user_logout.set_defaults(func=cmd_user_logout)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    rc = int(args.func(args) or 0)
    raise SystemExit(rc)
