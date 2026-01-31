import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


ALLOWED_SERVICES = {
    "pactown-network.service",
    "traefik.service",
    "api.service",
    "web.service",
    "postgres.service",
    "redis.service",
}

CONTAINER_TO_SERVICE = {
    "traefik": "traefik.service",
    "api": "api.service",
    "web": "web.service",
    "postgres": "postgres.service",
    "redis": "redis.service",
}


def _run(
    args: Sequence[str],
    *,
    check: bool = False,
    capture: bool = True,
    text: bool = True,
    timeout: Optional[int] = None,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        list(args),
        check=check,
        capture_output=capture,
        text=text,
        timeout=timeout,
    )


def _is_tty() -> bool:
    return bool(sys.stdin.isatty() and sys.stdout.isatty())


def _confirm(prompt: str) -> bool:
    try:
        ans = input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return ans == "y"


def _now() -> int:
    return int(time.time())


def _guard_dir() -> Path:
    base = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state")))
    return base / "pactown" / "guard"


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, data: Any) -> None:
    _write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def _extract_failures(diag: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    results = list(diag.get("results") or [])
    failures = [r for r in results if not bool(r.get("success"))]
    errors = [str(x) for x in (diag.get("errors") or [])]
    warnings = [str(x) for x in (diag.get("warnings") or [])]
    return failures, errors, warnings


def _simple_nlp_tags(messages: Sequence[str]) -> List[str]:
    joined = "\n".join(messages).lower()
    tags: List[str] = []
    rules = [
        (r"ipv6|aaaa", "dns_ipv6"),
        (r"tls|certificate|acme|letsencrypt", "tls"),
        (r"timeout|000\b|connection|refused", "connectivity"),
        (r"not active|failed", "service_down"),
        (r"router|hostregexp|traefik", "traefik_routing"),
        (r"localhost|127\.0\.0\.1|loopback", "localhost_leak"),
    ]
    for pat, tag in rules:
        if re.search(pat, joined):
            tags.append(tag)
    return sorted(set(tags))


def _state_path() -> Path:
    return _guard_dir() / "state.json"


def _load_state() -> Dict[str, Any]:
    p = _state_path()
    if not p.exists():
        return {"restarts": {}}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"restarts": {}}


def _save_state(state: Dict[str, Any]) -> None:
    _write_json(_state_path(), state)


def _rate_limit_ok(state: Dict[str, Any], service: str, *, window_sec: int, max_actions: int) -> bool:
    restarts = state.setdefault("restarts", {}).setdefault(service, [])
    now = _now()
    restarts[:] = [t for t in restarts if isinstance(t, int) and now - t < window_sec]
    return len(restarts) < max_actions


def _record_restart(state: Dict[str, Any], service: str) -> None:
    restarts = state.setdefault("restarts", {}).setdefault(service, [])
    restarts.append(_now())


def _looks_like_repo_root(p: Path) -> bool:
    return (p / "infra" / "scripts" / "diagnostics.sh").exists()


def _find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    if cur.is_file():
        cur = cur.parent
    for p in [cur, *cur.parents]:
        if _looks_like_repo_root(p):
            return p
    return start.resolve()


def _repo_root_from_installed() -> Path:
    # Prefer nearest repo root by walking up from CWD.
    return _find_repo_root(Path(os.getcwd()))


def run_diagnostics(*, prod: bool, repo_root: Path) -> Dict[str, Any]:
    script = repo_root / "infra" / "scripts" / "diagnostics.sh"
    if not script.exists():
        raise RuntimeError(f"diagnostics.sh not found at: {script}")

    cmd = ["bash", str(script), "--json"]
    cmd.append("--prod" if prod else "--dev")

    p = _run(cmd, check=False, timeout=180)
    if p.returncode not in (0, 1):
        raise RuntimeError(f"diagnostics.sh failed (exit={p.returncode}): {p.stderr.strip()}")

    try:
        return json.loads(p.stdout)
    except Exception as e:
        raise RuntimeError(
            f"Failed to parse diagnostics JSON. stderr={p.stderr.strip()} stdout_head={p.stdout[:200]!r}"
        ) from e


def propose_actions(diag: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    failures, errors, warnings = _extract_failures(diag)

    services_to_restart: List[str] = []
    reasons: List[str] = []

    for r in failures:
        cat = str(r.get("category") or "")
        if cat == "service":
            svc = str(r.get("service") or "")
            if svc in ALLOWED_SERVICES:
                services_to_restart.append(svc)
                reasons.append(f"service_failed:{svc}")
        elif cat == "container":
            c = str(r.get("container") or "")
            svc = CONTAINER_TO_SERVICE.get(c)
            if svc and svc in ALLOWED_SERVICES:
                services_to_restart.append(svc)
                reasons.append(f"container_failed:{c}")

    tags = _simple_nlp_tags(list(errors) + list(warnings))
    if "service_down" in tags and "api.service" not in services_to_restart:
        services_to_restart.append("api.service")
        reasons.append("nlp_tag:service_down")

    if "connectivity" in tags and "traefik.service" not in services_to_restart:
        services_to_restart.append("traefik.service")
        reasons.append("nlp_tag:connectivity")

    deduped: List[str] = []
    for s in services_to_restart:
        if s not in deduped:
            deduped.append(s)

    return deduped, reasons


def restart_services(services: Sequence[str]) -> None:
    if not services:
        return

    _run(["systemctl", "--user", "daemon-reload"], check=False)
    for svc in services:
        _run(["systemctl", "--user", "restart", svc], check=False)


def start_triage_tmux(*, session: str, repo_root: Path) -> bool:
    if not shutil.which("tmux"):
        return False

    exists = _run(["tmux", "has-session", "-t", session], check=False)
    if exists.returncode == 0:
        return True

    repo_dir = str(repo_root)

    _run(
        [
            "tmux",
            "new-session",
            "-d",
            "-s",
            session,
            "bash",
            "-lc",
            "journalctl --user -u traefik.service -n 200 -f --no-pager",
        ],
        check=False,
    )
    _run(
        [
            "tmux",
            "split-window",
            "-h",
            "-t",
            session,
            "bash",
            "-lc",
            "journalctl --user -u api.service -n 200 -f --no-pager",
        ],
        check=False,
    )
    _run(
        [
            "tmux",
            "split-window",
            "-v",
            "-t",
            session,
            "bash",
            "-lc",
            f"cd {repo_dir} && echo 'Try: make diag-prod' && exec bash",
        ],
        check=False,
    )

    return True


def _pip_user_install(args: Sequence[str]) -> int:
    pip = shutil.which("pip3") or shutil.which("pip")
    if not pip:
        print("ERROR: pip not found (install python3-pip)")
        return 2
    cmd = [pip, "install", "--user", "--upgrade", *args]
    print("RUN:", " ".join(shlex.quote(x) for x in cmd))
    p = _run(cmd, check=False, capture=False)
    return p.returncode


def cmd_install_self(*, editable: bool, repo_root: Optional[Path]) -> int:
    if not _is_tty():
        print("ERROR: pactown-guard install requires an interactive TTY")
        return 2

    resolved_repo = repo_root or _repo_root_from_installed()
    use_repo_install = bool(repo_root) or editable or _looks_like_repo_root(resolved_repo)

    if use_repo_install:
        target = str(resolved_repo)
        print("This will install pactown-guard from local repo (editable):")
        print(f"  {target}")
        if not _confirm("Proceed? [y/N] "):
            return 1
        return _pip_user_install(["-e", target])

    print("This will install/upgrade pactown-guard from PyPI (user install).")
    if not _confirm("Proceed? [y/N] "):
        return 1
    return _pip_user_install(["pactown-guard"])


def cmd_update_self(*, editable: bool, repo_root: Optional[Path]) -> int:
    if not _is_tty():
        print("ERROR: pactown-guard update requires an interactive TTY")
        return 2

    resolved_repo = repo_root or _repo_root_from_installed()
    use_repo_update = editable or (resolved_repo / ".git").exists()

    if not use_repo_update:
        print("This will upgrade pactown-guard from PyPI (user install).")
        if not _confirm("Proceed? [y/N] "):
            return 1
        return _pip_user_install(["pactown-guard"])

    if not shutil.which("git"):
        print("ERROR: git not found")
        return 2

    print("This will run: git -C <repo> pull and then reinstall pactown-guard from repo (-e).")
    print(f"  repo={resolved_repo}")
    if not _confirm("Proceed? [y/N] "):
        return 1

    p = _run(["git", "-C", str(resolved_repo), "pull"], check=False, capture=False, timeout=120)
    if p.returncode != 0:
        return p.returncode
    return _pip_user_install(["-e", str(resolved_repo)])


def _print_diag(diag: Dict[str, Any]) -> None:
    summary = diag.get("summary") or {}
    status = (summary.get("status") or "").lower()
    print(f"status={status} passed={summary.get('passed')} failed={summary.get('failed')} total={summary.get('total')}")

    failures, errors, warnings = _extract_failures(diag)

    if failures:
        print("\nFAILED checks:")
        for r in failures[:30]:
            name = r.get("name")
            cat = r.get("category")
            err = r.get("error")
            detail = err or ""
            print(f"- {name} [{cat}] {detail}")
        if len(failures) > 30:
            print(f"(and {len(failures) - 30} more)")

    if errors:
        print("\nErrors:")
        for e in errors[:30]:
            print(f"- {e}")

    if warnings:
        print("\nWarnings:")
        for w in warnings[:30]:
            print(f"- {w}")


def interactive_shell(*, prod: bool, repo_root: Path, max_restarts_per_15m: int) -> int:
    guard_dir = _guard_dir()
    guard_dir.mkdir(parents=True, exist_ok=True)
    state = _load_state()

    diag = run_diagnostics(prod=prod, repo_root=repo_root)
    _write_json(guard_dir / "last_diag.json", diag)
    _print_diag(diag)

    while True:
        try:
            line = input("pactown-guard> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("")
            return 0

        if not line:
            continue

        parts = shlex.split(line)
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in {"quit", "exit"}:
            return 0

        if cmd == "help":
            print("Commands:")
            print("  diag            - run diagnostics")
            print("  show            - show last diagnostics summary")
            print("  suggest         - suggest safe actions (no changes)")
            print("  apply           - apply suggested actions (asks for confirmation)")
            print("  restart <svc>   - restart a single systemd --user service")
            print("  logs <svc>      - tail journalctl for service")
            print("  triage          - open tmux triage session")
            print("  exit/quit       - leave")
            continue

        if cmd == "diag":
            diag = run_diagnostics(prod=prod, repo_root=repo_root)
            _write_json(guard_dir / "last_diag.json", diag)
            _print_diag(diag)
            continue

        if cmd == "show":
            _print_diag(diag)
            continue

        if cmd == "suggest":
            services, reasons = propose_actions(diag)
            failures, errors, warnings = _extract_failures(diag)
            tags = _simple_nlp_tags(list(errors) + list(warnings))
            _write_json(guard_dir / "last_tags.json", {"tags": tags, "reasons": reasons})
            print(f"tags={tags}")
            if services:
                print("suggested restarts:")
                for s in services:
                    print(f"- {s}")
            else:
                print("no suggested restarts")
            continue

        if cmd == "apply":
            services, reasons = propose_actions(diag)
            if not services:
                print("No suggested actions.")
                continue

            print("Suggested restarts:")
            for s in services:
                print(f"- {s}")
            print(f"reasons={reasons}")

            ok_services: List[str] = []
            for svc in services:
                if not _rate_limit_ok(state, svc, window_sec=15 * 60, max_actions=max_restarts_per_15m):
                    print(f"SKIP (rate-limit): {svc}")
                    continue
                ans = input(f"Restart {svc}? [y/N] ").strip().lower()
                if ans == "y":
                    ok_services.append(svc)

            if not ok_services:
                print("No restarts selected.")
                continue

            restart_services(ok_services)
            for s in ok_services:
                _record_restart(state, s)
            _save_state(state)

            time.sleep(3)
            diag = run_diagnostics(prod=prod, repo_root=repo_root)
            _write_json(guard_dir / "last_diag_after_actions.json", diag)
            _print_diag(diag)
            continue

        if cmd == "restart":
            if not args:
                print("Usage: restart <service>")
                continue
            svc = args[0]
            if svc not in ALLOWED_SERVICES:
                print(f"Refusing. Not in allowed services: {svc}")
                continue
            ans = input(f"Restart {svc}? [y/N] ").strip().lower()
            if ans != "y":
                continue
            if not _rate_limit_ok(state, svc, window_sec=15 * 60, max_actions=max_restarts_per_15m):
                print(f"SKIP (rate-limit): {svc}")
                continue
            restart_services([svc])
            _record_restart(state, svc)
            _save_state(state)
            continue

        if cmd == "logs":
            if not args:
                print("Usage: logs <service>")
                continue
            svc = args[0]
            _run(["journalctl", "--user", "-u", svc, "-n", "200", "--no-pager"], check=False, capture=False)
            continue

        if cmd == "triage":
            session = os.environ.get("PACTOWN_GUARD_TMUX_SESSION", "pactown-triage")
            started = start_triage_tmux(session=session, repo_root=repo_root)
            print(f"triage started={started} session={session}")
            continue

        print(f"Unknown command: {cmd}. Try: help")


def non_interactive_run(*, prod: bool, repo_root: Path) -> int:
    guard_dir = _guard_dir()
    guard_dir.mkdir(parents=True, exist_ok=True)

    diag = run_diagnostics(prod=prod, repo_root=repo_root)
    _write_json(guard_dir / "last_diag.json", diag)

    summary = diag.get("summary") or {}
    status = (summary.get("status") or "").lower()
    return 0 if status == "healthy" else 2


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=["run", "install", "update"],
        help="run: start guard shell; install: install pactown-guard; update: upgrade pactown-guard",
    )
    parser.add_argument("--prod", action="store_true", default=False)
    parser.add_argument("--dev", action="store_true", default=False)
    parser.add_argument("--repo", default="", help="Path to pactown-com repo root")
    parser.add_argument(
        "--editable",
        action="store_true",
        default=False,
        help="(install/update) use local repo (-e) instead of PyPI",
    )

    parser.add_argument("--interactive", action="store_true", default=False)
    parser.add_argument("--non-interactive", dest="interactive", action="store_false")

    parser.add_argument("--max-restarts-per-15m", type=int, default=3)

    args = parser.parse_args(list(argv) if argv is not None else None)

    prod = True
    if args.dev:
        prod = False
    if args.prod:
        prod = True

    repo_root = Path(args.repo).resolve() if args.repo else _repo_root_from_installed()

    if args.command == "install":
        return cmd_install_self(editable=args.editable, repo_root=repo_root if args.repo else None)

    if args.command == "update":
        return cmd_update_self(editable=args.editable, repo_root=repo_root if args.repo else None)

    interactive = args.interactive or _is_tty()
    if not interactive:
        return non_interactive_run(prod=prod, repo_root=repo_root)

    return interactive_shell(prod=prod, repo_root=repo_root, max_restarts_per_15m=args.max_restarts_per_15m)


if __name__ == "__main__":
    raise SystemExit(main())
