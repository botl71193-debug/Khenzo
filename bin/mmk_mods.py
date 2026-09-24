#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MMK MODS — All-in-One (Flutter + Hermes + MTCR)
Satu file: menu utama + Flutter Smali Patcher + MTCR Apply Tool
"""

import os
import sys
import time
from pathlib import Path


# ═══════════════════════════════════════════════════════════════
#  PATH LAYOUT (input / output / tools)
#  menu/
#  ├── app/          ← input APK/APKS
#  ├── out/
#  │   ├── protect/
#  │   ├── patched/
#  │   ├── app/
#  │   └── injected/
#  └── files/        ← apkeditor.jar, blutter, libs, ...
#  Prefer /home/app jika ada (server layout).
#  Override: export MMK_ROOT=... MMK_APP_DIR=...
# ═══════════════════════════════════════════════════════════════

def _mmk_detect_root():
    """
    Cari root project yang punya folder app/ atau files/ atau nama 'menu'.
    Urutan: MMK_ROOT env → walk-up dari __file__ → walk-up dari cwd → /home
    """
    env = os.environ.get("MMK_ROOT", "").strip()
    if env and os.path.isdir(env):
        return os.path.abspath(env)

    def _has_layout(path):
        if not path or not os.path.isdir(path):
            return False
        if os.path.isdir(os.path.join(path, "app")):
            return True
        if os.path.isdir(os.path.join(path, "files")):
            return True
        if os.path.basename(path.rstrip("/\\")) in ("menu", "Menu", "MMK", "mmk", "Zbot"):
            return True
        return False

    def _walk_up(start, max_levels=6):
        cur = os.path.abspath(start)
        for _ in range(max_levels):
            if _has_layout(cur):
                return cur
            # juga cek subfolder menu/
            sub = os.path.join(cur, "menu")
            if _has_layout(sub):
                return sub
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
        return None

    try:
        here = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        here = os.getcwd()

    for start in (here, os.getcwd(), "/storage/emulated/0/Zbot/menu", "/storage/emulated/0/Zbot", "/home"):
        hit = _walk_up(start)
        if hit:
            # prefer .../menu jika parent + menu/ sama-sama valid
            menu_sub = os.path.join(hit, "menu")
            if os.path.isdir(os.path.join(menu_sub, "app")) or os.path.isdir(os.path.join(menu_sub, "files")):
                return os.path.abspath(menu_sub)
            return os.path.abspath(hit)
    return os.path.abspath(here)


def _mmk_init_paths():
    """Hitung ulang path global (bisa dipanggil ulang setelah chdir)."""
    global MMK_ROOT, MMK_APP_DIR, MMK_OUT_DIR, MMK_OUT_PROTECT, MMK_OUT_PATCHED
    global MMK_OUT_APP, MMK_OUT_INJECTED, MMK_FILES_DIR

    MMK_ROOT = _mmk_detect_root()

    env_app = os.environ.get("MMK_APP_DIR", "").strip()
    candidates_app = []
    if env_app:
        candidates_app.append(os.path.abspath(env_app))
    candidates_app.extend([
        os.path.join(MMK_ROOT, "app"),
        os.path.join(MMK_ROOT, "menu", "app"),
        "/home/app",
        os.path.join(os.getcwd(), "app"),
        os.path.join(os.getcwd(), "menu", "app"),
    ])
    # pilih yang ada isinya dulu (apk/apks), prioritaskan menu/app
    MMK_APP_DIR = None
    filled = []
    empty = []
    for c in candidates_app:
        if not c:
            continue
        ac = os.path.abspath(c)
        if not os.path.isdir(ac):
            continue
        try:
            has = any(
                f.lower().endswith((".apk", ".apks", ".xapk", ".aab", ".apkm"))
                for f in os.listdir(ac)
                if os.path.isfile(os.path.join(ac, f))
            )
        except OSError:
            has = False
        if has:
            filled.append(ac)
        else:
            empty.append(ac)
    if filled:
        # prefer path yang mengandung '/menu/app'
        prefer = [p for p in filled if p.replace("\\", "/").endswith("/menu/app") or p.replace("\\", "/").endswith("/app")]
        MMK_APP_DIR = (prefer[0] if prefer else filled[0])
    elif empty:
        MMK_APP_DIR = empty[0]
    if not MMK_APP_DIR:
        # default: ROOT/app atau ROOT/menu/app
        for c in (os.path.join(MMK_ROOT, "menu", "app"), os.path.join(MMK_ROOT, "app")):
            MMK_APP_DIR = c
            break

    MMK_OUT_DIR = os.environ.get("MMK_OUT_DIR") or os.path.join(MMK_ROOT, "out")
    if not os.path.isdir(MMK_OUT_DIR) and os.path.isdir(os.path.join(MMK_ROOT, "menu", "out")):
        MMK_OUT_DIR = os.path.join(MMK_ROOT, "menu", "out")
    MMK_OUT_PROTECT = os.path.join(MMK_OUT_DIR, "protect")
    MMK_OUT_PATCHED = os.path.join(MMK_OUT_DIR, "patched")
    MMK_OUT_APP = os.path.join(MMK_OUT_DIR, "app")
    MMK_OUT_INJECTED = os.path.join(MMK_OUT_DIR, "injected")

    env_files = os.environ.get("MMK_FILES_DIR", "").strip()
    if env_files:
        MMK_FILES_DIR = os.path.abspath(env_files)
    else:
        for c in (
            os.path.join(MMK_ROOT, "files"),
            os.path.join(MMK_ROOT, "menu", "files"),
            os.path.join(os.getcwd(), "files"),
        ):
            if os.path.isdir(c):
                MMK_FILES_DIR = os.path.abspath(c)
                break
        else:
            MMK_FILES_DIR = os.path.join(MMK_ROOT, "files")


# init sekali saat import
_mmk_init_paths()


def mmk_ensure_dirs():
    _mmk_init_paths()  # refresh jika folder baru dibuat
    for d in (
        MMK_APP_DIR,
        MMK_OUT_DIR,
        MMK_OUT_PROTECT,
        MMK_OUT_PATCHED,
        MMK_OUT_APP,
        MMK_OUT_INJECTED,
        MMK_FILES_DIR,
        os.path.join(MMK_FILES_DIR, "libs"),
    ):
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass


def mmk_output(category, filename):
    """
    category: protect | patched | app | injected | default
    return absolute path di folder out yang sesuai
    """
    mmk_ensure_dirs()
    cat = (category or "app").lower()
    base = {
        "protect": MMK_OUT_PROTECT,
        "protected": MMK_OUT_PROTECT,
        "patched": MMK_OUT_PATCHED,
        "patch": MMK_OUT_PATCHED,
        "flutter": MMK_OUT_PATCHED,
        "hermes": MMK_OUT_PATCHED,
        "smali": MMK_OUT_PATCHED,
        "regex": MMK_OUT_PATCHED,
        "app": MMK_OUT_APP,
        "apk": MMK_OUT_APP,
        "session": MMK_OUT_APP,
        "batch": MMK_OUT_APP,
        "injected": MMK_OUT_INJECTED,
        "inject": MMK_OUT_INJECTED,
        "dialog": MMK_OUT_INJECTED,
        "default": MMK_OUT_APP,
    }.get(cat, MMK_OUT_APP)
    return os.path.join(base, os.path.basename(filename))


def mmk_list_apks(exts=(".apk", ".apks", ".xapk", ".aab", ".apkm")):
    """
    Scan APK dari lokasi input.
    Prioritas ketat: folder yang BENAR-BENAR berisi file matching.
    Selalu cek menu/app, Zbot/menu/app, /home/app.
    """
    mmk_ensure_dirs()
    _mmk_init_paths()  # refresh path jika user pindah folder
    seen = set()
    primary = []
    for d in (
        MMK_APP_DIR,
        os.path.join(MMK_ROOT, "app"),
        os.path.join(MMK_ROOT, "menu", "app"),
        "/home/app",
        os.path.join(os.getcwd(), "app"),
        os.path.join(os.getcwd(), "menu", "app"),
        "/storage/emulated/0/Zbot/menu/app",
        "/storage/emulated/0/Zbot/app",
        os.path.join(os.path.dirname(os.getcwd()), "menu", "app"),
        os.path.join(os.path.dirname(os.getcwd()), "app"),
    ):
        if not d:
            continue
        ad = os.path.abspath(d)
        if ad not in primary and os.path.isdir(ad):
            primary.append(ad)

    def _scan(dirlist):
        found = []
        for d in dirlist:
            try:
                names = sorted(os.listdir(d))
            except OSError:
                continue
            for f in names:
                low = f.lower()
                if not any(low.endswith(e) for e in exts):
                    continue
                fp = os.path.abspath(os.path.join(d, f))
                if fp in seen or not os.path.isfile(fp):
                    continue
                seen.add(fp)
                try:
                    sz = os.path.getsize(fp)
                except OSError:
                    sz = 0
                # tampilkan prefix folder biar jelas asal file
                try:
                    rel_dir = os.path.basename(d)
                    display = f"{rel_dir}/{f}" if rel_dir else f
                except Exception:
                    display = f
                found.append((fp, display, sz))
        return found

    # 1) folder yang punya file matching dulu
    with_files = []
    empty_ok = []
    for d in primary:
        chunk = _scan([d])
        if chunk:
            with_files.extend(chunk)
        else:
            empty_ok.append(d)
    if with_files:
        return with_files

    # 2) fallback cwd
    cwd = os.path.abspath(os.getcwd())
    if cwd not in primary:
        out = _scan([cwd])
        if out:
            return out

    # 3) kosong — caller akan tampilkan MMK_APP_DIR
    return []
    # dead code below kept for safety — unreachable
    for d in primary:
        if d not in dirs:
            dirs.append(d)
    for d in dirs:
        try:
            names = sorted(os.listdir(d))
        except OSError:
            continue
        for f in names:
            low = f.lower()
            if not any(low.endswith(e) for e in exts):
                continue
            fp = os.path.abspath(os.path.join(d, f))
            if fp in seen or not os.path.isfile(fp):
                continue
            seen.add(fp)
            try:
                sz = os.path.getsize(fp)
            except OSError:
                sz = 0
            # tampilkan path relatif singkat di nama
            display = f
            try:
                if os.path.abspath(d) != os.path.abspath(os.getcwd()):
                    display = f"{os.path.basename(d)}/{f}"
            except Exception:
                pass
            out.append((fp, display, sz))
    return out


def mmk_find_in_files(*names_or_globs):
    """Cari file di FILES_DIR lalu ROOT lalu cwd."""
    import glob as _glob
    roots = []
    for r in (MMK_FILES_DIR, os.path.join(MMK_ROOT, "files"), MMK_ROOT, os.getcwd()):
        if r and os.path.isdir(r) and r not in roots:
            roots.append(r)
    found = []
    for root in roots:
        for pat in names_or_globs:
            exact = os.path.join(root, pat)
            if os.path.isfile(exact):
                found.append(exact)
            try:
                for hit in _glob.glob(os.path.join(root, "**", pat), recursive=True):
                    if os.path.isfile(hit):
                        found.append(hit)
                for hit in _glob.glob(os.path.join(root, pat)):
                    if os.path.isfile(hit):
                        found.append(hit)
            except Exception:
                pass
    seen = set()
    uniq = []
    for f in found:
        a = os.path.abspath(f)
        if a not in seen:
            seen.add(a)
            uniq.append(a)
    return uniq


def mmk_print_paths():
    print(f"  {_LC.DIM}ROOT  : {MMK_ROOT}{_LC.RESET}")
    print(f"  {_LC.DIM}APP   : {MMK_APP_DIR}{_LC.RESET}")
    print(f"  {_LC.DIM}OUT   : {MMK_OUT_DIR}{_LC.RESET}")
    print(f"  {_LC.DIM}FILES : {MMK_FILES_DIR}{_LC.RESET}")



class _LC:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"


def _clear():
    os.system("clear" if os.name != "nt" else "cls")


def _mmk_sysinfo():
    """Info sistem ala neofetch (Termux / Linux / Kali)."""
    import platform as _plat
    import socket
    info = {}
    try:
        user = os.environ.get("USER") or os.environ.get("LOGNAME") or "user"
        host = socket.gethostname() or "localhost"
        info["user"] = f"{user}@{host}"
    except Exception:
        info["user"] = "mmk@localhost"
    try:
        if os.path.isdir("/data/data/com.termux"):
            rel = ""
            model = ""
            try:
                with open("/system/build.prop", "r", errors="ignore") as f:
                    props = f.read()
                for line in props.splitlines():
                    if line.startswith("ro.build.version.release="):
                        rel = line.split("=", 1)[1].strip()
                    if line.startswith("ro.product.model="):
                        model = line.split("=", 1)[1].strip()
            except Exception:
                pass
            arch = _plat.machine() or "aarch64"
            info["os"] = f"Android {rel} {arch}".strip() if rel else f"Android {arch}"
            info["host"] = model or "Android Device"
        else:
            pretty = _plat.platform()
            try:
                if os.path.isfile("/etc/os-release"):
                    with open("/etc/os-release", "r") as f:
                        for line in f:
                            if line.startswith("PRETTY_NAME="):
                                pretty = line.split("=", 1)[1].strip().strip('"')
                                break
            except Exception:
                pass
            info["os"] = pretty
            info["host"] = _plat.node()
    except Exception:
        info["os"] = _plat.system()
        info["host"] = _plat.node()
    try:
        info["kernel"] = _plat.release()
    except Exception:
        info["kernel"] = "-"
    try:
        info["arch"] = _plat.machine() or "unknown"
    except Exception:
        info["arch"] = "unknown"
    try:
        sh = os.environ.get("SHELL", "/bin/bash")
        info["shell"] = os.path.basename(sh)
        if os.path.isfile(sh):
            try:
                out = subprocess.check_output([sh, "--version"], stderr=subprocess.DEVNULL, text=True, timeout=2)
                info["shell"] = out.splitlines()[0].strip()[:36]
            except Exception:
                pass
    except Exception:
        info["shell"] = "bash"
    info["term"] = os.environ.get("TERM") or "unknown"
    if "com.termux" in str(os.environ.get("PREFIX", "")) or os.path.isdir("/data/data/com.termux"):
        info["term"] = "com.termux"
    try:
        cpu = _plat.processor() or ""
        if not cpu and os.path.isfile("/proc/cpuinfo"):
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if line.startswith("Hardware") or line.startswith("model name") or line.startswith("Processor"):
                        cpu = line.split(":", 1)[-1].strip()
                        break
        info["cpu"] = (cpu or "unknown")[:32]
    except Exception:
        info["cpu"] = "unknown"
    try:
        if os.path.isfile("/proc/meminfo"):
            mem_t = mem_a = 0
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        mem_t = int(line.split()[1])
                    elif line.startswith("MemAvailable:"):
                        mem_a = int(line.split()[1])
            used = max(0, (mem_t - mem_a) // 1024)
            total = mem_t // 1024
            info["memory"] = f"{used}MiB / {total}MiB"
        else:
            info["memory"] = "-"
    except Exception:
        info["memory"] = "-"
    try:
        with open("/proc/uptime", "r") as f:
            sec = float(f.read().split()[0])
        days = int(sec // 86400)
        hours = int((sec % 86400) // 3600)
        mins = int((sec % 3600) // 60)
        info["uptime"] = f"{days} days, {hours} hours, {mins} mins" if days else f"{hours} hours, {mins} mins"
    except Exception:
        info["uptime"] = "-"
    try:
        if shutil.which("dpkg"):
            n = max(0, len(subprocess.check_output(["dpkg", "-l"], stderr=subprocess.DEVNULL, text=True).splitlines()) - 5)
            info["packages"] = f"{n} (dpkg)"
        else:
            info["packages"] = "-"
    except Exception:
        info["packages"] = "-"
    info["python"] = f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    info["support"] = "arm64 · armeabi-v7a · x86_64"
    info["suite"] = "Flutter · Hermes · Smali · Protect"
    return info


def _banner_mmk():
    """Banner Termux-style: ASCII kiri + sysinfo kanan + strip path."""
    mmk_ensure_dirs()
    si = _mmk_sysinfo()
    is_termux = (
        "com.termux" in str(os.environ.get("PREFIX", ""))
        or os.path.isdir("/data/data/com.termux")
        or "termux" in str(si.get("term", "")).lower()
    )
    # Siluet naga (merah) — tanpa teks
    art = [
        r"..............                         ",
        r" .............::::...                  ",
        r"  ..........:::::::::..                ",
        r"   ........:::::::::::::..             ",
        r"    ......:::::::::::::::::.           ",
        r"     ....::::::::::::::::::::.         ",
        r"      ...:::::::'''::::::::::::.       ",
        r"       ..:::::'     ':::::::::::.      ",
        r"        .::::  ,--.  ::::::::::::.     ",
        r"         .::: ( 00 ) :::::::::::::.    ",
        r"          .::  `--'  ::::::::::::::.   ",
        r"           .:       .::::::::::::::.   ",
        r"            .........::::::::::::::.   ",
        r"                    .::::::::::::::.   ",
        r"                     .:::::::::::::'   ",
        r"                      .::::::::::'     ",
        r"                       ':::::::'       ",
        r"                         '''''         ",
    ]
    _aw = max(len(x) for x in art)
    art = [x.ljust(_aw) for x in art]
    _BOLD_RED = "\033[1;91m"
    _GREEN = "\033[1;92m"
    _CYAN = "\033[1;96m"
    user = si.get("user", "mmk@host")
    labels = [
        ("OS", si.get("os", "-")),
        ("Host", si.get("host", "-")),
        ("Kernel", si.get("kernel", "-")),
        ("Uptime", si.get("uptime", "-")),
        ("Packages", si.get("packages", "-")),
        ("Shell", si.get("shell", "-")),
        ("Terminal", si.get("term", "-") + (" · Termux" if is_termux else "")),
        ("CPU", si.get("cpu", "-")),
        ("Memory", si.get("memory", "-")),
        ("Arch", si.get("arch", "-")),
        ("Support", si.get("support", "-")),
        ("Python", si.get("python", "-")),
        ("Suite", si.get("suite", "-")),
    ]
    print()
    # header strip ala Termux
    print(f"  {_GREEN}╭──────────────────────────────────────────────────────────╮{_LC.RESET}")
    title = "MMK MOD  ·  TERMUX SUITE" if is_termux else "MMK MOD  ·  ALL-IN-ONE"
    print(f"  {_GREEN}│{_LC.RESET}  {_LC.BOLD}{_CYAN}{title:<54}{_LC.RESET}{_GREEN}│{_LC.RESET}")
    print(f"  {_GREEN}╰──────────────────────────────────────────────────────────╯{_LC.RESET}")
    print()
    print(f"  {_LC.BOLD}{_CYAN}{user}{_LC.RESET}")
    print(f"  {_LC.DIM}{'-' * max(12, len(user))}{_LC.RESET}")
    max_n = max(len(art), len(labels))
    for i in range(max_n):
        left = art[i] if i < len(art) else " " * _aw
        if i < len(labels):
            key, val = labels[i]
            # potong val agar tidak wrap di layar Termux sempit
            val_s = str(val)
            if len(val_s) > 36:
                val_s = val_s[:33] + "..."
            right = f"{_CYAN}{key:<10}{_LC.RESET}: {val_s}"
        else:
            right = ""
        print(f"  {_BOLD_RED}{left}{_LC.RESET}  {right}")
    # color bar
    bar = "  " + " " * _aw + "  "
    for c in (_LC.RED, _LC.GREEN, _LC.YELLOW, _LC.BLUE, _LC.MAGENTA, _LC.CYAN, _LC.WHITE):
        bar += f"{c}██{_LC.RESET}"
    print()
    print(bar)
    print()
    # path strip
    print(f"  {_GREEN}┌ path ────────────────────────────────────────────────────┐{_LC.RESET}")
    print(f"  {_GREEN}│{_LC.RESET} {_LC.DIM}APP  {_LC.RESET}{MMK_APP_DIR}")
    print(f"  {_GREEN}│{_LC.RESET} {_LC.DIM}OUT  {_LC.RESET}{MMK_OUT_DIR}/{{protect,patched,app,injected}}")
    print(f"  {_GREEN}│{_LC.RESET} {_LC.DIM}FILES{_LC.RESET} {MMK_FILES_DIR}")
    print(f"  {_GREEN}└─────────────────────────────────────────────────────────┘{_LC.RESET}")
    print()


def _mmk_main_menu():
    mmk_ensure_dirs()
    while True:
        _clear()
        _banner_mmk()
        if mmk_session_active():
            mmk_session_print_bar()
            print()
        # ── Menu 3 kolom (hemat ruang) ──────────────────────────
        items = [
            ("1",  "Flutter"),
            ("2",  "Hermes"),
            ("3",  "Smali"),
            ("4",  "MTCR Tool"),
            ("5",  "Nexus Toolkit"),
            ("6",  "Sign APK"),
            ("7",  "Protect APK"),
            ("8",  "Inject Dialog"),
            ("9",  "APKS → APK"),
            ("10", "PairIP Bypass"),
            ("11", "Multibypass"),
            ("12", "History"),
            ("13", "Hook App"),
            ("14", "About"),
            ("15", "Work Session"),
            ("16", "Revengi"),
            ("17", "WA Bot"),
            ("18", "REGEX PRO"),
            ("19", "Buka Proteksi"),
            ("20", "Protect Script"),
            ("21", "DEX Anti-Bingung"),
            ("22", "Premium Scan"),
        ]
        cols = 3

        print(f"  {_LC.BOLD}{_LC.GREEN}┌{'─'*22}┬{'─'*22}┬{'─'*22}┐{_LC.RESET}")
        print(
            f"  {_LC.BOLD}{_LC.GREEN}│{_LC.RESET}{_LC.BOLD}{'  MENU · TERMUX'.center(22)}{_LC.RESET}"
            f"{_LC.BOLD}{_LC.GREEN}│{_LC.RESET}{_LC.BOLD}{'  PATCH · UTILS'.center(22)}{_LC.RESET}"
            f"{_LC.BOLD}{_LC.GREEN}│{_LC.RESET}{_LC.BOLD}{'  EXTRA · TOOLS'.center(22)}{_LC.RESET}"
            f"{_LC.BOLD}{_LC.GREEN}│{_LC.RESET}"
        )
        print(f"  {_LC.BOLD}{_LC.GREEN}├{'─'*22}┼{'─'*22}┼{'─'*22}┤{_LC.RESET}")
        # isi per baris: 1,6,11 | 2,7,12 | ...
        n = len(items)
        rows = (n + cols - 1) // cols
        for r in range(rows):
            cells = []
            for c in range(cols):
                # kolom c: item index r + c*rows  → layout vertikal per kolom
                # user minta: 1 6 11 / 2 7 12  → berarti baris = nomor berurutan horizontal per grup 6
                # layout: col0 = 1..6, col1 = 7..12, col2 = 13..18  OR  row-wise 1,6,11
                # User example: 1 6 11 ; 2 7 12 → index = r + c*6 for 18 items with 6 rows
                idx = r + c * rows
                if idx < n:
                    num, name = items[idx]
                    cell = f" {_LC.GREEN}{num:>2}){_LC.RESET} {name}"
                    # pad visible width ~22 (tanpa ANSI)
                    visible = f" {num:>2}) {name}"
                    pad = max(0, 22 - len(visible))
                    cells.append(cell + (" " * pad))
                else:
                    cells.append(" " * 22)
            print(
                f"  {_LC.CYAN}│{_LC.RESET}{cells[0]}{_LC.CYAN}│{_LC.RESET}"
                f"{cells[1]}{_LC.CYAN}│{_LC.RESET}{cells[2]}{_LC.CYAN}│{_LC.RESET}"
            )
        print(f"  {_LC.BOLD}{_LC.GREEN}└{'─'*22}┴{'─'*22}┴{'─'*22}┘{_LC.RESET}")
        print()
        print(f"  {_LC.DIM}[ 0 ] EXIT{_LC.RESET}  {_LC.GREEN}·{_LC.RESET}  {_LC.DIM}Termux: pakai font monospace · warna 256{_LC.RESET}")
        print()
        choice = input(f"  {_LC.MAGENTA}▶ 𝚙𝚒𝚕𝚒𝚑 𝚗𝚘𝚖𝚘𝚛 ➤{_LC.RESET} ").strip()

        if choice == "1":
            try:
                flutter_main()
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print(f"\n{_LC.YELLOW}Dibatalkan{_LC.RESET}")
            except Exception as e:
                print(f"  {_LC.RED}✗{_LC.RESET} Flutter error: {e}")
                import traceback
                traceback.print_exc()
            input(f"\n{_LC.YELLOW}Press Enter to return...{_LC.RESET}")

        elif choice == "2":
            try:
                hermes_main()
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print(f"\n{_LC.YELLOW}Dibatalkan{_LC.RESET}")
            except Exception as e:
                print(f"  {_LC.RED}✗{_LC.RESET} Hermes error: {e}")
                import traceback
                traceback.print_exc()
            input(f"\n{_LC.YELLOW}Press Enter to return...{_LC.RESET}")

        elif choice == "3":
            try:
                smali_main()
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print(f"\n{_LC.YELLOW}Dibatalkan{_LC.RESET}")
            except Exception as e:
                print(f"  {_LC.RED}✗{_LC.RESET} Smali error: {e}")
                import traceback
                traceback.print_exc()
            input(f"\n{_LC.YELLOW}Press Enter to return...{_LC.RESET}")

        elif choice == "4":
            try:
                global CONFIG, USE_COLORS, VERBOSE, DRY_RUN
                CONFIG = load_config()
                USE_COLORS = CONFIG.get("use_colors", True) and supports_color()
                VERBOSE = CONFIG.get("verbose_mode", False)
                DRY_RUN = False
                setup_logging()
                if not check_python():
                    input("Press Enter...")
                    continue
                if not check_java():
                    input("Press Enter...")
                    continue
                check_disk_space(silent=True)
                main_menu()  # MTCR
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print(f"\n{_LC.YELLOW}Kembali ke MMK MODS{_LC.RESET}")
            except Exception as e:
                print(f"  {_LC.RED}✗{_LC.RESET} MTCR error: {e}")
                import traceback
                traceback.print_exc()
                input(f"\n{_LC.YELLOW}Press Enter...{_LC.RESET}")

        elif choice == "5":
            try:
                toolkit_main()
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print(f"\n{_LC.YELLOW}Kembali ke MMK MODS{_LC.RESET}")
            except Exception as e:
                print(f"  {_LC.RED}✗{_LC.RESET} Toolkit error: {e}")
                import traceback
                traceback.print_exc()
            input(f"\n{_LC.YELLOW}Press Enter to return...{_LC.RESET}")

        elif choice == "6":
            try:
                sign_apk_main()
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print(f"\n{_LC.YELLOW}Dibatalkan{_LC.RESET}")
            except Exception as e:
                print(f"  {_LC.RED}✗{_LC.RESET} Sign error: {e}")
                import traceback
                traceback.print_exc()
            input(f"\n{_LC.YELLOW}Press Enter to return...{_LC.RESET}")

        elif choice == "7":
            try:
                protect_apk_main()
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print(f"\n{_LC.YELLOW}Dibatalkan{_LC.RESET}")
            except Exception as e:
                print(f"  {_LC.RED}✗{_LC.RESET} Protect error: {e}")
                import traceback
                traceback.print_exc()
            input(f"\n{_LC.YELLOW}Press Enter to return...{_LC.RESET}")

        elif choice == "8":
            try:
                inject_dialog_main()
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print(f"\n{_LC.YELLOW}Dibatalkan{_LC.RESET}")
            except Exception as e:
                print(f"  {_LC.RED}✗{_LC.RESET} Inject error: {e}")
                import traceback
                traceback.print_exc()
            input(f"\n{_LC.YELLOW}Press Enter to return...{_LC.RESET}")

        elif choice == "9":
            try:
                apks_to_apk_main()
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print(f"\n{_LC.YELLOW}Dibatalkan{_LC.RESET}")
            except Exception as e:
                print(f"  {_LC.RED}✗{_LC.RESET} APKS convert error: {e}")
                import traceback
                traceback.print_exc()
            input(f"\n{_LC.YELLOW}Press Enter to return...{_LC.RESET}")

        elif choice == "10":
            try:
                pairip_bypass_main()
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print(f"\n{_LC.YELLOW}Dibatalkan{_LC.RESET}")
            except Exception as e:
                print(f"  {_LC.RED}✗{_LC.RESET} PairIP error: {e}")
                import traceback
                traceback.print_exc()
            input(f"\n{_LC.YELLOW}Press Enter to return...{_LC.RESET}")

        elif choice == "11":
            try:
                multibypass_main()
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print(f"\n{_LC.YELLOW}Dibatalkan{_LC.RESET}")
            except Exception as e:
                print(f"  {_LC.RED}✗{_LC.RESET} Multibypass error: {e}")
                import traceback
                traceback.print_exc()
            input(f"\n{_LC.YELLOW}Press Enter to return...{_LC.RESET}")

        elif choice == "12":
            try:
                history_mmk_main()
            except Exception as e:
                print(f"  {_LC.RED}✗{_LC.RESET} History error: {e}")
                import traceback
                traceback.print_exc()
            input(f"\n{_LC.YELLOW}Press Enter to return...{_LC.RESET}")

        elif choice == "13":
            try:
                hook_app_main()
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print(f"\n{_LC.YELLOW}Dibatalkan{_LC.RESET}")
            except Exception as e:
                print(f"  {_LC.RED}✗{_LC.RESET} Hook App error: {e}")
                import traceback
                traceback.print_exc()
            input(f"\n{_LC.YELLOW}Press Enter to return...{_LC.RESET}")

        elif choice == "14":
            try:
                about_mmk()
            except Exception as e:
                print(f"  {_LC.RED}✗{_LC.RESET} {e}")
            input(f"\n{_LC.YELLOW}Press Enter to return...{_LC.RESET}")

        elif choice == "15":
            try:
                work_session_main()
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print(f"\n{_LC.YELLOW}Dibatalkan{_LC.RESET}")
            except Exception as e:
                print(f"  {_LC.RED}✗{_LC.RESET} Session error: {e}")
                import traceback
                traceback.print_exc()
            input(f"\n{_LC.YELLOW}Press Enter to return...{_LC.RESET}")

        elif choice == "16":
            try:
                revengi_toolkit_main()
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print(f"\n{_LC.YELLOW}Dibatalkan{_LC.RESET}")
            except Exception as e:
                print(f"  {_LC.RED}✗{_LC.RESET} Revengi Toolkit error: {e}")
                import traceback
                traceback.print_exc()
            input(f"\n{_LC.YELLOW}Press Enter to return...{_LC.RESET}")

        elif choice == "17":
            try:
                wa_bot_menu()
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print(f"\n{_LC.YELLOW}Dibatalkan{_LC.RESET}")
            except Exception as e:
                print(f"  {_LC.RED}✗{_LC.RESET} WA Bot error: {e}")
                import traceback
                traceback.print_exc()
            input(f"\n{_LC.YELLOW}Press Enter to return...{_LC.RESET}")

        elif choice == "18":
            try:
                ads_regex_main()
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print(f"\n{_LC.YELLOW}Dibatalkan{_LC.RESET}")
            except Exception as e:
                print(f"  {_LC.RED}✗{_LC.RESET} Ads Regex error: {e}")
                import traceback
                traceback.print_exc()
            input(f"\n{_LC.YELLOW}Press Enter to return...{_LC.RESET}")

        elif choice == "19":
            try:
                unprotect_apk_main()
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print(f"\n{_LC.YELLOW}Dibatalkan{_LC.RESET}")
            except Exception as e:
                print(f"  {_LC.RED}✗{_LC.RESET} Buka Proteksi error: {e}")
                import traceback
                traceback.print_exc()
            input(f"\n{_LC.YELLOW}Press Enter to return...{_LC.RESET}")

        elif choice == "20":
            try:
                protect_script_main()
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print(f"\n{_LC.YELLOW}Dibatalkan{_LC.RESET}")
            except Exception as e:
                print(f"  {_LC.RED}✗{_LC.RESET} Protect Script error: {e}")
                import traceback
                traceback.print_exc()
            input(f"\n{_LC.YELLOW}Press Enter to return...{_LC.RESET}")

        elif choice == "21":
            try:
                dex_anti_confusion_main()
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print(f"\n{_LC.YELLOW}Dibatalkan{_LC.RESET}")
            except Exception as e:
                print(f"  {_LC.RED}✗{_LC.RESET} DEX Anti-Bingung error: {e}")
                import traceback
                traceback.print_exc()
            input(f"\n{_LC.YELLOW}Press Enter to return...{_LC.RESET}")

        elif choice == "22":
            try:
                premium_logic_scan_main()
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print(f"\n{_LC.YELLOW}Dibatalkan{_LC.RESET}")
            except Exception as e:
                print(f"  {_LC.RED}✗{_LC.RESET} Premium Scan error: {e}")
                import traceback
                traceback.print_exc()
            input(f"\n{_LC.YELLOW}Press Enter to return...{_LC.RESET}")

        elif choice == "0":
            if mmk_session_active():
                print(f"  {_LC.YELLOW}Session masih aktif — build dulu (15) atau abort{C.RESET}" if False else "")
                ans = input(f"  {_LC.YELLOW}Session aktif. Abort & exit? [y/N] ➤{_LC.RESET} ").strip().lower()
                if ans in ("y", "ya", "yes"):
                    mmk_session_abort()
                else:
                    continue
            print()
            print(f"  {_LC.CYAN}›{_LC.RESET} Thanks — MMK MODS")
            print()
            sys.exit(0)
        else:
            print(f"  {_LC.YELLOW}⚠{_LC.RESET} Pilihan tidak valid")
            time.sleep(0.7)


# ═══════════════════════════════════════════════════════════════
#  SECTION: FLUTTER SMALI PATCHER
# ═══════════════════════════════════════════════════════════════



import os  ## untuk operasi sistem dan file
import sys  ## untuk akses argumen dan fungsi sistem
import shutil  ## untuk operasi file/folder seperti copy dan hapus
import json  ## untuk baca/tulis data JSON
import re  ## untuk regular expression/pencarian pola teks
import zipfile  ## untuk membaca dan membuat file ZIP
import tempfile  ## untuk membuat file atau folder sementara
import subprocess  ## untuk menjalankan perintah shell
import urllib.request  ## untuk mengambil data dari URL
import glob  ## untuk mencari file dengan pola tertentu
import time  ## untuk delay atau waktu
import traceback  ## untuk menampilkan detail error
import r2pipe  ## untuk berkomunikasi dengan Radare2
import threading


# ═══════════════════════════════════════════════════════════════
#  COOL TERMINAL UI HELPERS  (ANSI + animations)
# ═══════════════════════════════════════════════════════════════

class C:
    """ANSI color codes"""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    BG_DARK = "\033[48;5;235m"
    BG_BLUE = "\033[44m"
    BG_MAG  = "\033[45m"

def clear_line():
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()


def _term_clear_lines(n):
    """Hapus n baris ke atas (efek seperti bot Telegram hapus/edit pesan)."""
    if not n or n <= 0:
        return
    try:
        for _ in range(int(n)):
            sys.stdout.write("\033[1A\033[2K")
        sys.stdout.flush()
    except Exception:
        pass


def status_ephemeral(msg, hold=0.5, ok_mark=True):
    """
    Tampilkan status sementara lalu hapus.
      Mencari : apkeditor.jar  [ ✓ ]
    → (hilang setelah hold detik)
    """
    mark = f"{C.GREEN}[ ✓ ]{C.RESET}" if ok_mark else f"{C.YELLOW}[ … ]{C.RESET}"
    sys.stdout.write(f"  {C.CYAN}›{C.RESET}  {msg}  {mark}\n")
    sys.stdout.flush()
    time.sleep(max(0.12, float(hold)))
    _term_clear_lines(1)


def status_search(what, hold=0.4):
    status_ephemeral(f"Mencari : {what}", hold=hold, ok_mark=True)


def status_prepare(what, hold=0.4):
    status_ephemeral(f"Menyiapkan : {what}", hold=hold, ok_mark=True)


def spinner(msg, duration=1.5, frames=None, keep=False):
    """
    Spinner animasi. Default: setelah selesai baris dihapus (gaya bot).
    keep=True → biarkan ✓ tetap tampil.
    """
    if frames is None:
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    end = time.time() + duration
    i = 0
    while time.time() < end:
        frame = frames[i % len(frames)]
        sys.stdout.write(f"\r  {C.CYAN}{frame}{C.RESET} {msg}   ")
        sys.stdout.flush()
        time.sleep(0.08)
        i += 1
    clear_line()
    if keep:
        print(f"  {C.GREEN}✓{C.RESET} {msg}")
    # else: dihapus — tidak print apa-apa

def progress_bar(current, total, prefix="", width=30, clear_when_done=False):
    """
    Progress bar satu baris.
    clear_when_done=True → hapus baris setelah 100% (gaya bot).
    """
    if total == 0:
        total = 1
    pct = current / total
    filled = int(width * pct)
    bar = "█" * filled + "░" * (width - filled)
    sys.stdout.write(f"\r  {prefix} {C.CYAN}[{bar}]{C.RESET} {pct*100:5.1f}%   ")
    sys.stdout.flush()
    if current >= total:
        if clear_when_done:
            sys.stdout.write("\r\033[K")
            sys.stdout.flush()
        else:
            print()

def banner(title, subtitle=None):
    """Cool boxed banner with gradient-style edges"""
    width = 62
    print()
    print(f"  {C.MAGENTA}╔{'═'*width}╗{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}{C.BOLD}{C.CYAN}{title.center(width)}{C.RESET}{C.MAGENTA}║{C.RESET}")
    if subtitle:
        print(f"  {C.MAGENTA}║{C.RESET}{C.DIM}{subtitle.center(width)}{C.RESET}{C.MAGENTA}║{C.RESET}")
    print(f"  {C.MAGENTA}╚{'═'*width}╝{C.RESET}")

def section(title):
    """Section header"""
    pad = max(1, 52 - len(title))
    print(f"\n  {C.BLUE}╭─ {C.BOLD}{C.WHITE}{title}{C.RESET}{C.BLUE} {'─'*pad}╮{C.RESET}")

def section_end():
    print(f"  {C.BLUE}╰{'─'*56}╯{C.RESET}")

def ok(msg):
    print(f"  {C.GREEN}✔{C.RESET}  {msg}")

def warn(msg):
    print(f"  {C.YELLOW}▲{C.RESET}  {msg}")

def err(msg):
    print(f"  {C.RED}✖{C.RESET}  {msg}")

def info(msg):
    print(f"  {C.CYAN}›{C.RESET}  {msg}")

def step(n, total, msg):
    print(f"  {C.MAGENTA}[{n}/{total}]{C.RESET} {msg}")

def divider(char="─", n=58):
    print(f"  {C.DIM}{char * n}{C.RESET}")


def box_info(lines, title=None, width=62):
    """Kotak info ringkas (✔ list / status)."""
    if isinstance(lines, str):
        lines = [lines]
    lines = [str(x) for x in lines if x is not None]
    print(f"  {C.CYAN}╔{'═'*width}╗{C.RESET}")
    if title:
        print(f"  {C.CYAN}║{C.RESET}{C.BOLD}{title.center(width)}{C.RESET}{C.CYAN}║{C.RESET}")
        print(f"  {C.CYAN}╠{'═'*width}╣{C.RESET}")
    for ln in lines:
        # strip long paths for display
        s = ln
        if len(s) > width - 4:
            s = s[: width - 7] + "..."
        print(f"  {C.CYAN}║{C.RESET}  {s:<{width-4}}{C.CYAN}║{C.RESET}")
    print(f"  {C.CYAN}╚{'═'*width}╝{C.RESET}")


def box_cmd_short(action, inp, outp, extra=None, width=62):
    """Ringkas CMD + direktori output."""
    out_dir = ""
    if outp:
        out_dir = os.path.dirname(os.path.abspath(outp)) or os.getcwd()
    lines = [
        f"Action : {action}",
        f"Input  : {os.path.basename(inp) if inp else '-'}",
        f"Output : {os.path.basename(outp) if outp else '-'}",
        f"Direktori : {out_dir or '-'}",
    ]
    if extra:
        lines.append(str(extra))
    box_info(lines, title="JOB", width=width)


def menu_table(rows, headers=("NO", "FITUR", "KETERANGAN"), width_cols=None):
    """
    rows: list of (no, name, desc)
    tampil tabel rapi
    """
    w0, w1, w2 = width_cols or (4, 22, 28)
    total = w0 + w1 + w2 + 8
    print(f"  {C.DIM}{'─'*total}{C.RESET}")
    print(
        f"  {C.YELLOW}{headers[0]:<{w0}}{C.RESET} "
        f"{C.YELLOW}{headers[1]:<{w1}}{C.RESET} "
        f"{C.YELLOW}{headers[2]:<{w2}}{C.RESET}"
    )
    print(f"  {C.DIM}{'─'*total}{C.RESET}")
    for no, name, desc in rows:
        print(
            f"  {C.GREEN}{str(no):<{w0}}{C.RESET} "
            f"{C.WHITE}{str(name):<{w1}}{C.RESET} "
            f"{C.DIM}{str(desc):<{w2}}{C.RESET}"
        )
    print(f"  {C.DIM}{'─'*total}{C.RESET}")


def progress_live(pct, label="", width=28):
    """Progress bar satu baris (overwrite)."""
    pct = max(0.0, min(100.0, float(pct)))
    filled = int(width * pct / 100)
    bar = chr(0x2588) * filled + chr(0x2591) * (width - filled)
    lab = (label or "")[:28]
    msg = "\r  " + C.CYAN + "[" + bar + "]" + C.RESET + " " + C.BOLD + ("%5.1f%%" % pct) + C.RESET + "  " + C.DIM + lab + C.RESET + "   "
    sys.stdout.write(msg)
    sys.stdout.flush()


def run_java_quiet(cmd, label="proses", timeout=None, keep_on_error=True):
    """
    Jalankan java -jar; log APKEditor TIDAK pernah ditampilkan.
    UI gaya bot Telegram:
      • saat jalan → box RUNNING + progress
      • sukses     → box + progress DIHAPUS, tinggal  ✔  LABEL selesai
      • gagal      → box diganti ERROR (tidak dihapus) + cuplikan log
    """
    import re as _re
    import threading

    tool = os.path.basename(cmd[2]) if len(cmd) > 2 else "java"
    width = 62
    body = [
        f"Engine : {label}",
        f"Tool   : {tool}",
        "Status : running (log disembunyikan)",
    ]
    # baris box: top, title, sep, body×3, bottom = 6
    block_lines = 2 + 1 + len(body) + 1
    print(f"  {C.CYAN}╔{'═'*width}╗{C.RESET}")
    print(f"  {C.CYAN}║{C.RESET}{C.BOLD}{'RUNNING'.center(width)}{C.RESET}{C.CYAN}║{C.RESET}")
    print(f"  {C.CYAN}╠{'═'*width}╣{C.RESET}")
    for ln in body:
        s = ln if len(ln) <= width - 4 else ln[: width - 7] + "..."
        print(f"  {C.CYAN}║{C.RESET}  {s:<{width-4}}{C.CYAN}║{C.RESET}")
    print(f"  {C.CYAN}╚{'═'*width}╝{C.RESET}")

    log_lines = []
    run_java_quiet.last_log = []

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )
    except Exception as e:
        _term_clear_lines(block_lines)
        err(f"Gagal start: {e}")
        run_java_quiet.last_log = [str(e)]
        return 1

    state = {"pct": 2.0, "label": "start", "dex_total": 0, "dex_done": 0, "done": False}

    def reader():
        try:
            for line in proc.stdout:
                raw = line.rstrip("\n")
                if raw:
                    log_lines.append(raw)
                    if len(log_lines) > 100:
                        del log_lines[:30]
                line = raw.strip()
                if not line:
                    continue
                # parse progress hints — jangan print log
                m = _re.search(r"Confusing\s+(\d+)\s+dex", line, _re.I)
                if m:
                    state["dex_total"] = max(1, int(m.group(1)))
                    state["label"] = f"dex 0/{state['dex_total']}"
                    state["pct"] = 15.0
                    continue
                m = _re.search(r"DexConfuser:\s*(classes\d*\.dex)", line, _re.I)
                if m:
                    state["dex_done"] += 1
                    tot = state["dex_total"] or max(state["dex_done"], 1)
                    state["pct"] = 15.0 + 80.0 * min(state["dex_done"], tot) / tot
                    state["label"] = f"{m.group(1)} ({state['dex_done']}/{tot})"
                    continue
                m = _re.search(r"Baksmali:\s*v?\d*[<>]?\s*(\d+)", line, _re.I)
                if m:
                    n = int(m.group(1))
                    state["pct"] = min(92.0, 10.0 + min(n, 2000) / 2000.0 * 80.0)
                    state["label"] = f"baksmali {n}"
                    continue
                low = line.lower()
                if "[build]" in low or "scanning" in low or "encoding" in low:
                    state["pct"] = min(95.0, state["pct"] + 1.2)
                    if "scanning" in low:
                        state["label"] = "scan"
                    elif "encoding" in low:
                        state["label"] = "encode"
                    elif "writing" in low or "saved" in low:
                        state["pct"] = 96.0
                        state["label"] = "write"
                    else:
                        state["label"] = "build"
                    continue
                if "[DECOMPILE]" in line or "Decompil" in line:
                    state["pct"] = max(state["pct"], min(88.0, state["pct"] + 1.5))
                    if "Saved to" in line:
                        state["pct"] = 96.0
                        state["label"] = "saved"
                    elif "Extracting" in line:
                        state["label"] = "extract"
                    else:
                        state["label"] = "decompile"
                    continue
                if "DirectoryConfuser" in line:
                    state["pct"] = max(state["pct"], 8.0)
                    state["label"] = "dirs"
                elif "FileNameConfuser" in line:
                    state["pct"] = max(state["pct"], 12.0)
                    state["label"] = "filenames"
                elif "TableConfuser" in line:
                    state["pct"] = max(state["pct"], 18.0)
                    state["label"] = "table"
                elif "Writing apk" in line or "Saved to" in line or "[PROTECT] Writing" in line:
                    state["pct"] = max(state["pct"], 95.0)
                    state["label"] = "writing"
                elif "Using:" in line or "APKEditor version" in line:
                    state["pct"] = max(state["pct"], 5.0)
                    state["label"] = "init"
                else:
                    if state["pct"] < 98:
                        state["pct"] = min(98.0, state["pct"] + 0.12)
                        if state["label"] in ("start", "warn", ""):
                            state["label"] = "working"
        except Exception:
            pass
        finally:
            state["done"] = True

    th = threading.Thread(target=reader, daemon=True)
    th.start()
    try:
        while proc.poll() is None:
            progress_live(state["pct"], state["label"])
            time.sleep(0.12)
        th.join(timeout=5)
        ok_rc = (proc.returncode == 0)
        progress_live(100.0 if ok_rc else state["pct"], "done" if ok_rc else "fail")
        sys.stdout.write("\n")
        sys.stdout.flush()

        if ok_rc:
            # SUKSES: hapus box + progress (seperti bot hapus pesan)
            _term_clear_lines(block_lines + 1)
            sys.stdout.write(f"  {C.GREEN}✔{C.RESET}  {label}\n")
            sys.stdout.flush()
            time.sleep(0.28)
            _term_clear_lines(1)
        else:
            # GAGAL: tampilkan ERROR box — JANGAN dihapus
            _term_clear_lines(block_lines + 1)
            print(f"  {C.RED}╔{'═'*width}╗{C.RESET}")
            print(f"  {C.RED}║{C.RESET}{C.BOLD}{C.RED}{'ERROR'.center(width)}{C.RESET}{C.RED}║{C.RESET}")
            print(f"  {C.RED}╠{'═'*width}╣{C.RESET}")
            for ln in (
                f"Engine : {label}",
                f"Tool   : {tool}",
                f"Status : gagal (code {proc.returncode})",
            ):
                s = ln if len(ln) <= width - 4 else ln[: width - 7] + "..."
                print(f"  {C.RED}║{C.RESET}  {s:<{width-4}}{C.RED}║{C.RESET}")
            print(f"  {C.RED}╚{'═'*width}╝{C.RESET}")
            if log_lines:
                print(f"  {C.YELLOW}── detail (error) ──{C.RESET}")
                for ln in log_lines[-8:]:
                    print(f"  {C.DIM}{ln[:96]}{C.RESET}")
            print(f"  {C.RED}✖{C.RESET}  {label} gagal")
    except KeyboardInterrupt:
        try:
            proc.kill()
        except Exception:
            pass
        sys.stdout.write("\n")
        sys.stdout.flush()
        _term_clear_lines(block_lines + 1)
        warn("Dibatalkan")
        run_java_quiet.last_log = log_lines[-30:]
        return 130

    run_java_quiet.last_log = log_lines[-40:]
    return proc.returncode if proc.returncode is not None else 1


def run_java_quiet_show_errors(max_lines=12):
    """Cuplikan log terakhir (hanya dipanggil manual saat error)."""
    logs = getattr(run_java_quiet, "last_log", None) or []
    if not logs:
        return
    print(f"  {C.YELLOW}── log (error) ──{C.RESET}")
    for ln in logs[-max_lines:]:
        print(f"  {C.DIM}{ln[:100]}{C.RESET}")



def human_size(nbytes):
    """Convert bytes to human readable size"""
    for unit in ["B", "KB", "MB", "GB"]:
        if nbytes < 1024:
            return f"{nbytes:.2f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.2f} TB"

# APK yang dipilih sekali di Multibypass — select_target memakai ini otomatis
MMK_PRESELECTED_APK = None
# Preset submenu Multibypass (isi sebelum eksekusi), contoh: {"9": "2", "7": "1"}
MMK_PRESET_OPTIONS = {}

# ── Work Session: decompile SEKALI → banyak patch → build di akhir ──
# Dipakai saat user jalankan beberapa fitur (smali, inject, pairip, hook)
# yang sama-sama butuh folder decompile.
MMK_SESSION = {
    "active": False,
    "apk": None,       # path APK sumber
    "dec": None,       # folder decompile
    "jar": None,       # APKEditor.jar
    "base": None,      # stem nama file
    "ops": [],         # log operasi yang sudah dijalankan
    "dirty": False,    # ada perubahan smali/manifest?
}


def mmk_session_active():
    return bool(MMK_SESSION.get("active") and MMK_SESSION.get("dec") and os.path.isdir(MMK_SESSION["dec"]))


def mmk_session_status_line():
    if not MMK_SESSION.get("active"):
        return ""
    ops = MMK_SESSION.get("ops") or []
    return f"SESSION · {os.path.basename(MMK_SESSION.get('apk') or '?')} · ops:{len(ops)} · {'DIRTY' if MMK_SESSION.get('dirty') else 'clean'}"


def mmk_session_print_bar():
    if not MMK_SESSION.get("active"):
        return
    print(f"  {C.BG_MAG}{C.BOLD}{C.WHITE} ⚡ WORK SESSION {C.RESET} {C.DIM}{mmk_session_status_line()}{C.RESET}")
    if MMK_SESSION.get("ops"):
        print(f"  {C.DIM}  done: {', '.join(MMK_SESSION['ops'][-6:])}{C.RESET}")


def mmk_session_start(apk_path, jar_abs=None, force_new=False):
    """
    Mulai / reuse session. Decompile hanya jika belum ada.
    Return path folder decompile atau None.
    """
    global MMK_SESSION
    apk_path = os.path.abspath(apk_path)
    if not jar_abs:
        try:
            jar_abs = _find_or_fetch_apkeditor() if "_find_or_fetch_apkeditor" in globals() else None
        except Exception:
            jar_abs = None
        if not jar_abs:
            try:
                jar_abs = _smali_ensure_apkeditor()
            except Exception:
                pass
    if not jar_abs:
        err("APKEditor.jar diperlukan untuk session")
        return None
    jar_abs = os.path.abspath(jar_abs)

    # reuse jika APK sama
    if (
        not force_new
        and MMK_SESSION.get("active")
        and MMK_SESSION.get("apk") == apk_path
        and MMK_SESSION.get("dec")
        and os.path.isdir(MMK_SESSION["dec"])
    ):
        ok(f"Reuse decompile: {os.path.basename(MMK_SESSION['dec'])}")
        info("Skip decompile — lanjut patch di folder yang sama")
        return MMK_SESSION["dec"]

    base = os.path.splitext(os.path.basename(apk_path))[0]
    dec = os.path.abspath(f"_mmk_session_{base}")
    if os.path.isdir(dec):
        spinner("Bersihkan session lama...", 0.4)
        shutil.rmtree(dec, ignore_errors=True)

    banner("SESSION DECOMPILE", "sekali saja · patch berkali-kali · build di akhir")
    box_cmd_short("decompile", apk_path, dec, "session · 1x")
    rc = run_java_quiet(["java", "-jar", jar_abs, "d", "-i", apk_path, "-o", dec, "-f"], label="DECOMPILE")
    if rc != 0 or not os.path.isdir(dec):
        rc = run_java_quiet(["java", "-jar", jar_abs, "d", "-i", apk_path, "-o", dec], label="DECOMPILE retry")
    if rc != 0 or not os.path.isdir(dec):
        err("Decompile gagal — session tidak dimulai")
        return None
    ok(f"Decompiled → {os.path.basename(dec)}")

    MMK_SESSION.update({
        "active": True,
        "apk": apk_path,
        "dec": dec,
        "jar": jar_abs,
        "base": base,
        "ops": ["decompile"],
        "dirty": False,
    })
    return dec


def mmk_session_log(op_name, dirty=True):
    if not MMK_SESSION.get("active"):
        return
    MMK_SESSION["ops"].append(op_name)
    if dirty:
        MMK_SESSION["dirty"] = True
    info(f"Session +{op_name} (total {len(MMK_SESSION['ops'])} ops)")


def mmk_session_finish(out_name=None, keep_dec=False):
    """Build sekali di akhir session. Return path output apk atau None."""
    global MMK_SESSION
    if not mmk_session_active():
        warn("Tidak ada session aktif")
        return None
    jar = MMK_SESSION["jar"]
    dec = MMK_SESSION["dec"]
    base = MMK_SESSION["base"] or "mmk"
    out_apk = mmk_output("app", out_name or f"{base}-session.apk")
    if os.path.exists(out_apk):
        try:
            os.remove(out_apk)
        except Exception:
            pass

    banner("SESSION BUILD", "compile semua patch sekaligus")
    mmk_session_print_bar()
    box_cmd_short("build", dec, out_apk, "session finish")
    rc = run_java_quiet(["java", "-jar", jar, "b", "-i", dec, "-o", out_apk, "-f"], label="BUILD")
    if rc != 0 or not os.path.isfile(out_apk):
        warn("Retry build -dex-lib jf")
        run_java_quiet(["java", "-jar", jar, "b", "-i", dec, "-o", out_apk, "-f", "-dex-lib", "jf"], label="BUILD jf")
    if not os.path.isfile(out_apk):
        run_java_quiet(["java", "-jar", jar, "b", "-i", dec, "-o", out_apk], label="BUILD retry")
    if not os.path.isfile(out_apk):
        err("Build session gagal")
        return None

    try:
        sz = human_size(os.path.getsize(out_apk))
    except Exception:
        sz = "-"
    out_dir = os.path.dirname(os.path.abspath(out_apk)) or os.getcwd()
    print()
    print(f"  {C.MAGENTA}╔{'═'*58}╗{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}{C.BOLD}{C.GREEN}{'SESSION COMPLETE'.center(58)}{C.RESET}{C.MAGENTA}║{C.RESET}")
    print(f"  {C.MAGENTA}╠{'═'*58}╣{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  Output    : {C.CYAN}{os.path.basename(out_apk)}{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  Size      : {sz}")
    print(f"  {C.MAGENTA}║{C.RESET}  Ops       : {', '.join(MMK_SESSION.get('ops') or [])}")
    print(f"  {C.MAGENTA}║{C.RESET}  Direktori : {C.CYAN}{out_dir[:44]}{C.RESET}")
    if len(out_dir) > 44:
        print(f"  {C.MAGENTA}║{C.RESET}              {C.DIM}{out_dir[44:88]}{C.RESET}")
    print(f"  {C.MAGENTA}╚{'═'*58}╝{C.RESET}")
    warn("Sign (menu 6) sebelum install")

    if not keep_dec:
        shutil.rmtree(dec, ignore_errors=True)
    MMK_SESSION.update({
        "active": False, "apk": None, "dec": None, "jar": None,
        "base": None, "ops": [], "dirty": False,
    })
    return out_apk


def mmk_session_abort():
    global MMK_SESSION
    dec = MMK_SESSION.get("dec")
    if dec and os.path.isdir(dec):
        shutil.rmtree(dec, ignore_errors=True)
    MMK_SESSION.update({
        "active": False, "apk": None, "dec": None, "jar": None,
        "base": None, "ops": [], "dirty": False,
    })
    warn("Session dibatalkan — folder decompile dihapus")


def work_session_main():
    """
    UI Work Session:
      decompile 1x → pilih patch berulang → build 1x di akhir
    """
    banner("WORK SESSION", "decompile sekali · multi patch · build akhir")
    info("Credit: MMK MOD")
    print()
    print(f"  {C.DIM}Ideal untuk: Smali + PairIP + Hook + Inject tanpa decompile berulang{C.RESET}")
    print()

    if mmk_session_active():
        mmk_session_print_bar()
        print(f"  {C.GREEN}1){C.RESET}  Lanjut session (tambah patch)")
        print(f"  {C.GREEN}2){C.RESET}  Finish → BUILD sekarang")
        print(f"  {C.GREEN}3){C.RESET}  Abort session")
        print(f"  {C.RED}0){C.RESET}  Kembali")
        c = input(f"  {C.MAGENTA}➤{C.RESET} ").strip()
        if c == "2":
            mmk_session_finish()
            return
        if c == "3":
            mmk_session_abort()
            return
        if c == "0":
            return
        # else lanjut submenu patch
    else:
        if not shutil.which("java"):
            err("Java diperlukan")
            return
        entries = mmk_list_apks()
        if not entries:
            err(f"Tidak ada APK di {MMK_APP_DIR}")
            return
        apk = select_target(entries, title="SESSION · PILIH APK") if "select_target" in globals() else os.path.abspath(apks[0])
        if not apk:
            return
        apk = os.path.abspath(apk)
        jar = None
        try:
            jar = _find_or_fetch_apkeditor()
        except Exception:
            pass
        if apk.lower().endswith((".apks", ".xapk")) and jar:
            merged = os.path.splitext(apk)[0] + "_merged.apk"
            run_java_quiet(["java", "-jar", jar, "m", "-i", apk, "-o", merged, "-f"], label="MERGE")
            if os.path.isfile(merged):
                apk = merged
        if not mmk_session_start(apk, jar):
            return

    # submenu patch (tanpa build)
    while mmk_session_active():
        _clear()
        banner("SESSION PATCH", "pilih fitur · belum di-build")
        mmk_session_print_bar()
        print()
        print(f"  {C.BOLD}{C.CYAN}▶ PATCH (reuse decompile){C.RESET}")
        print(f"     {C.GREEN}1){C.RESET}  Smali / Premium regex")
        print(f"     {C.GREEN}2){C.RESET}  PairIP bypass (smali+manifest)")
        print(f"     {C.GREEN}3){C.RESET}  Hook methods (input isPremium dll)")
        print(f"     {C.GREEN}4){C.RESET}  Inject Dialog (dex + onCreate)")
        print()
        print(f"  {C.BOLD}{C.YELLOW}▶ FINISH{C.RESET}")
        print(f"     {C.GREEN}9){C.RESET}  BUILD sekali & tutup session")
        print(f"     {C.RED}0){C.RESET}  Kembali (session tetap hidup)")
        print()
        ch = input(f"  {C.MAGENTA}➤{C.RESET} ").strip()
        dec = MMK_SESSION["dec"]

        if ch == "0":
            info("Session tetap aktif — masuk menu 15 lagi untuk finish")
            return
        if ch == "9":
            mmk_session_finish()
            return
        if ch == "1":
            try:
                n = _smali_walk_and_patch(dec)
                try:
                    _smali_patch_pairip_manifest(dec)
                except Exception:
                    pass
                mmk_session_log(f"smali({n})")
                ok(f"Smali patch applied ({n})")
            except Exception as e:
                err(str(e))
            input(f"\n  {C.DIM}Enter...{C.RESET}")
        elif ch == "2":
            try:
                # pairip smali patterns on existing dec
                if "PAIRIP_SMALI_PATTERNS" in globals() or "MMK_SMALI_PATTERNS" in globals():
                    _smali_walk_and_patch(dec)
                try:
                    _smali_patch_pairip_manifest(dec)
                except Exception as e:
                    warn(str(e))
                # also dedicated pairip if exists
                try:
                    if "_pairip_patch_manifest" in globals():
                        man = None
                        for root, _, fs in os.walk(dec):
                            if "AndroidManifest.xml" in fs:
                                man = os.path.join(root, "AndroidManifest.xml")
                                break
                        if man:
                            _pairip_patch_manifest(man)
                except Exception as e:
                    warn(str(e))
                mmk_session_log("pairip")
                ok("PairIP patch applied")
            except Exception as e:
                err(str(e))
            input(f"\n  {C.DIM}Enter...{C.RESET}")
        elif ch == "3":
            try:
                rules = _hook_collect_rules()
                if not rules:
                    warn("Tidak ada rule")
                else:
                    n, details = _hook_patch_smali_methods(dec, rules)
                    mmk_session_log(f"hook({n})")
                    ok(f"Hook patched {n} method(s)")
                    for d in details[:10]:
                        print(f"  {C.DIM}{d}{C.RESET}")
            except Exception as e:
                err(str(e))
            input(f"\n  {C.DIM}Enter...{C.RESET}")
        elif ch == "4":
            info("Inject Dialog butuh DEX + Activity — jalankan dari menu 8")
            info("atau paste dex ke session manual")
            try:
                inject_dialog_main()
                mmk_session_log("inject")
            except Exception as e:
                err(str(e))
            input(f"\n  {C.DIM}Enter...{C.RESET}")
        else:
            warn("Pilihan tidak valid")
            time.sleep(0.5)


def select_target(files, title="SELECT TARGET"):
    """
    Beautiful interactive file selection menu.
    files: list of (path, display_name, size_bytes)
    Returns selected path or None if exit.
    Jika MMK_PRESELECTED_APK diset (mode Multibypass), langsung pakai tanpa tanya lagi.
    Auto-scan MMK_APP_DIR (/home/app atau ROOT/app) jika files kosong.
    """
    global MMK_PRESELECTED_APK
    if not files:
        files = mmk_list_apks()
    if not files:
        err(f"Tidak ada APK di: {MMK_APP_DIR}")
        info("Letakkan file .apk/.apks di folder app/")
        return None

    # Multibypass: skip pilih ulang
    if MMK_PRESELECTED_APK:
        pre = os.path.abspath(MMK_PRESELECTED_APK)
        for path, name, size in files:
            if os.path.abspath(path) == pre or name == os.path.basename(pre):
                ok(f"APK preselect: {name}")
                return path
        if os.path.isfile(pre):
            ok(f"APK preselect: {os.path.basename(pre)}")
            return pre

    while True:
        # hitung baris UI agar bisa dihapus setelah pilih (gaya bot)
        # empty + top + title + sep + header + sep + N rows + sep + exit + bottom + empty + prompt
        n_rows = len(files)
        ui_lines = 1 + 1 + 1 + 1 + 1 + 1 + n_rows + 1 + 1 + 1 + 1 + 1

        print()
        tw = 66
        print(f"  {C.CYAN}┌{'─'*tw}┐{C.RESET}")
        print(f"  {C.CYAN}│{C.RESET}{C.BOLD}{C.WHITE}{title.center(tw)}{C.RESET}{C.CYAN}│{C.RESET}")
        print(f"  {C.CYAN}├{'─'*4}┬{'─'*48}┬{'─'*12}┤{C.RESET}")
        print(
            f"  {C.CYAN}│{C.RESET}{C.YELLOW}{' NO ':>4}{C.RESET}{C.CYAN}│{C.RESET}"
            f"{C.YELLOW}{' FILENAME':<48}{C.RESET}{C.CYAN}│{C.RESET}"
            f"{C.YELLOW}{' SIZE':>12}{C.RESET}{C.CYAN}│{C.RESET}"
        )
        print(f"  {C.CYAN}├{'─'*4}┼{'─'*48}┼{'─'*12}┤{C.RESET}")

        for i, (path, name, size) in enumerate(files, 1):
            size_str = human_size(size)
            display = name if len(name) <= 46 else name[:43] + "..."
            print(
                f"  {C.CYAN}│{C.RESET}{C.GREEN}{i:3d} {C.RESET}{C.CYAN}│{C.RESET}"
                f" {C.WHITE}{display:<47}{C.RESET}{C.CYAN}│{C.RESET}"
                f"{C.CYAN}{size_str:>12}{C.RESET}{C.CYAN}│{C.RESET}"
            )

        print(f"  {C.CYAN}├{'─'*4}┼{'─'*48}┼{'─'*12}┤{C.RESET}")
        print(
            f"  {C.CYAN}│{C.RESET}{C.RED}{'  0 ':>4}{C.RESET}{C.CYAN}│{C.RESET}"
            f" {C.RED}{'EXIT / KELUAR':<47}{C.RESET}{C.CYAN}│{C.RESET}"
            f"{'':>12}{C.CYAN}│{C.RESET}"
        )
        print(f"  {C.CYAN}└{'─'*4}┴{'─'*48}┴{'─'*12}┘{C.RESET}")

        try:
            choice = input(f"\n  {C.MAGENTA}𝙿𝚒𝚕𝚒𝚑 𝚗𝚘𝚖𝚘𝚛 ➤{C.RESET} ").strip()
            if choice == "0" or choice.lower() in ("exit", "keluar", "q"):
                _term_clear_lines(ui_lines)
                return None
            idx = int(choice)
            if 1 <= idx <= len(files):
                selected = files[idx - 1]
                # hapus tabel + prompt (input line juga)
                _term_clear_lines(ui_lines)
                # konfirmasi singkat lalu hilang
                status_ephemeral(
                    f"Dipilih : {selected[1]}  ({human_size(selected[2])})",
                    hold=0.45,
                    ok_mark=True,
                )
                return selected[0]
            else:
                warn("Nomor tidak valid. Coba lagi.")
                time.sleep(0.6)
                _term_clear_lines(1)
                _term_clear_lines(ui_lines)
        except ValueError:
            warn("Masukkan angka saja.")
            time.sleep(0.6)
            _term_clear_lines(1)
            _term_clear_lines(ui_lines)
        except KeyboardInterrupt:
            print()
            _term_clear_lines(ui_lines)
            return None

def animate_startup():
    """Cool startup animation — MMK MODS"""
    logo = [
        r"  ███╗   ███╗███╗   ███╗██╗  ██╗    ███╗   ███╗ ██████╗ ██████╗ ███████╗",
        r"  ████╗ ████║████╗ ████║██║ ██╔╝    ████╗ ████║██╔═══██╗██╔══██╗██╔════╝",
        r"  ██╔████╔██║██╔████╔██║█████╔╝     ██╔████╔██║██║   ██║██║  ██║███████╗",
        r"  ██║╚██╔╝██║██║╚██╔╝██║██╔═██╗     ██║╚██╔╝██║██║   ██║██║  ██║╚════██║",
        r"  ██║ ╚═╝ ██║██║ ╚═╝ ██║██║  ██╗    ██║ ╚═╝ ██║╚██████╔╝██████╔╝███████║",
        r"  ╚═╝     ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝    ╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝",
    ]
    print()
    for line in logo:
        print(f"{C.CYAN}{line}{C.RESET}")
        time.sleep(0.04)
    print(f"{C.MAGENTA}{'═'*72}{C.RESET}")
    print(f"{C.BOLD}{C.WHITE}{'FLUTTER SMALI PATCHER  •  MMK MODS EDITION'.center(72)}{C.RESET}")
    print(f"{C.DIM}{'⚡ Premium / VIP / Subscription Bypass Engine ⚡'.center(72)}{C.RESET}")
    print(f"{C.MAGENTA}{'═'*72}{C.RESET}")
    time.sleep(0.3)


ENABLE_FLUTTER_PATCH = True   ## mengaktifkan patch untuk bagian Flutter
ENABLE_MANIFEST_PATCH = True  ## mengaktifkan patch pada AndroidManifest
ENABLE_AUTO_INSTALL = False   ## menonaktifkan instalasi otomatis


ENABLE_PP_PATCH = False       ## patch PP dimatikan
ENABLE_ASM_PATCH = True       ## patch ASM diaktifkan


KEYWORDS_TRUE = ["keyword", "keyword"] ## daftar kata kunci yang dianggap positif/benar
KEYWORDS_FALSE = ["SVIP", "isSvip", "Svip", "SvipState", "Subscription", "dailyAdKey", "pro_access_life_time", "premiumstatus", "premium", "Premium_is_active", "isPro", "isvip", "vip", "ispremium", "is_premium", "is_vip", "is_pro", "lifetime", "CustomerInfo", "isSubscription", "issubscribe"]  ## daftar kata kunci yang biasanya dianggap negatif/tidak aktif


ENABLE_TRUE_PATCH = False  ## patch untuk kondisi true dimatikan
ENABLE_FALSE_PATCH = True   ## patch untuk kondisi false diaktifkan

ASM_REGEX_PATTERNS = [
    # Regex 1
    r"(((SVIP|premium|Svip|SvipState|vip|subscribed|_getUserActivationStatus|Subscription|dailyAdKey|pro_access_life_time|premiumstatus|Premium_is_active|isPremium|isSubscription|ispro\b|is_pro\b|is_premium|is_subscription)\w*\s*\([^)]*\)\s*(?:async\s*)?\{?)|(entitlementinfo)|(customerinfo))(?:[\s\S]*?)}",
    
    # Regex 2
    r"((?:\b(?:get|fetch|retrieve)?issubscription|islifetime|get.*subscription.*info|subscription.*status|plus|subscription.*controller|is_lifetime|has.*lifetime|\w*lifetime\b|\blifetime\w*|is subscription|isSubscription|issubscription\b|has.*subscription|\bispro\b|pro_access|\bhaspro\b|\bis.*pro\b|has_premium|hasPremium|get.*PREMIUM|subscribed|is_subscribed|setpremium|set_premium|isPremium|vip|has.*access|isvip|hasvip|Svip|vip|is_premium|has_vip|hasvip|svipstate|get.*VIP|is_subscription)(?:(?!\/\/ \*\* addr:).)*?\n\s*\/\/ \*\* addr: .*, size:)(?:[\s\S]*?)}"
]

ASM_FALSE_PATTERNS = [
    r"(\b0x[0-9a-fA-F]+):\s*(?:r\d+|x\d+|w\d+)\s*=\s*false", ## mendeteksi instruksi yang langsung meng-set register menjadi false
    r"(\b0x[0-9a-fA-F]+).*false\b",  ## mencari baris yang mengandung false
    r"^(\b0x[0-9a-fA-F]+):.*\bfalse" ## mencari baris awal yang mengandung false
]



def check_termux():
    return os.path.exists('/data/data/com.termux/files/usr/bin') ## mengecek apakah path bin Termux ada, artinya script berjalan di Termux

def install_packages():
    banner("CHECKING REQUIRED PACKAGES", "Termux dependency installer")
    
    packages = [
        "openjdk-17", "python", "git", "cmake", "ninja", 
        "build-essential", "pkg-config", "libicu", "capstone", 
        "fmt", "wget", "unzip"
    ]
    
    pip_packages = ["requests", "pyelftools", "r2pipe"]
    
    try:
        spinner("Updating package list...", 1.2)
        subprocess.run(["pkg", "update", "-y"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        total = len(packages)
        for i, pkg in enumerate(packages, 1):
            progress_bar(i-1, total, f"pkg {pkg}")
            result = subprocess.run(["pkg", "list-installed", pkg], capture_output=True, text=True)
            if result.returncode != 0 or pkg not in result.stdout:
                subprocess.run(["pkg", "install", "-y", pkg], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                ok(f"{pkg} installed")
            else:
                ok(f"{pkg} already installed")
            progress_bar(i, total, f"pkg {pkg}")
        
        section("Python packages")
        for pip_pkg in pip_packages:
            try:
                __import__(pip_pkg.replace("-", "_"))
                ok(f"{pip_pkg} already installed")
            except ImportError:
                spinner(f"Installing {pip_pkg}...", 1.0)
                subprocess.run([sys.executable, "-m", "pip", "install", pip_pkg], check=True)
                ok(f"{pip_pkg} installed")
        section_end()
        
        banner("ALL PACKAGES READY", "Environment is good to go")
        return True
        
    except Exception as e:
        err(f"Package installation error: {e}")
        return False

def install_blutter():
    banner("CHECKING BLUTTER", "Flutter AOT dump tool")
    
    home = os.path.expanduser("~")
    blutter_dir = os.path.join(home, "blutter-termux")
    
    if os.path.exists(blutter_dir) and os.path.exists(os.path.join(blutter_dir, "blutter.py")):
        ok("Blutter already installed")
        return True
    
    try:
        spinner("Cloning Blutter repository...", 2.0)
        subprocess.run(["git", "clone", "https://github.com/AbhiTheModder/blutter-termux.git", blutter_dir], 
                      check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        ok("Blutter downloaded")
        
        os.chdir(blutter_dir)
        spinner("Patching std::format → fmt::format...", 1.0)
        subprocess.run(["find", ".", "-type", "f", "-exec", "sed", "-i", "s/std::format/fmt::format/g", "{}", "+"],
                      check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        ok("Files updated")
        
        os.chdir(home)
        ok("Blutter successfully installed and configured")
        return True
        
    except Exception as e:
        err(f"Blutter installation error: {e}")
        return False

def check_and_install_r2():
    banner("CHECKING RADARE2", "Disassembler & binary patcher")
    
    if shutil.which("r2"):
        ok("Radare2 already installed")
        return True
    
    try:
        spinner("Installing Radare2 via pkg...", 2.5)
        subprocess.run(["pkg", "install", "-y", "radare2"], 
                      check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if shutil.which("r2"):
            ok("Radare2 successfully installed")
            return True
        else:
            err("Radare2 installation failed")
            return False
            
    except Exception as e:
        err(f"Radare2 installation error: {e}")
        return False

def check_and_install_pptool():
    banner("CHECKING PPTOOL", "Pointer pool finder")
    
    if shutil.which("pptool"):
        ok("Pptool already installed")
        return True
    
    try:
        spinner("Cloning & compiling pptool...", 2.0)
        home = os.path.expanduser("~")
        pptool_dir = os.path.join(home, "ppfind")
        
        if os.path.exists(pptool_dir):
            shutil.rmtree(pptool_dir)
        
        subprocess.run(["git", "clone", "https://github.com/Pr0214/ppfind", pptool_dir], 
                      check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        os.chdir(pptool_dir)
        subprocess.run(["g++", "-std=c++11", "-o", "pptool", "pptool.cpp"], 
                      check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["chmod", "+x", "pptool"], check=True)
        shutil.copy("pptool", "/data/data/com.termux/files/usr/bin/")
        os.chdir(home)
        
        if shutil.which("pptool"):
            ok("Pptool successfully installed")
            return True
        else:
            err("Pptool installation failed")
            return False
            
    except Exception as e:
        err(f"Pptool installation error: {e}")
        return False

def run_auto_installation():
    if not check_termux():
        err("This script should only be run in Termux environment!")
        return False
    
    banner("AUTO INSTALLATION MODE", "Installing all required tools...")
    
    try:
        if not install_packages():
            err("Package installation failed!")
            return False
        
        if not install_blutter():
            err("Blutter installation failed!")
            return False
        
        if not check_and_install_r2():
            err("Radare2 installation failed!")
            return False
        
        if not check_and_install_pptool():
            err("Pptool installation failed!")
            return False
        
        jar_file = check_apkeditor()
        if not jar_file:
            err("APKEditor installation failed!")
            return False
        
        banner("AUTO INSTALLATION COMPLETED!", "Flutter Smali Patcher is ready")
        return True
        
    except Exception as e:
        err(f"Auto installation error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def check_apkeditor():
    """Check and download APKEditor (FILES_DIR → cwd)"""
    banner("CHECKING APKEDITOR", "APK decompile / rebuild engine")
    mmk_ensure_dirs()
    found = mmk_find_in_files("apkeditor.jar", "APKEditor.jar", "*APKEditor*.jar", "*apkeditor*.jar")
    if found:
        ok(f"APKEditor found: {found[0]}")
        return found[0]
    try:
        for f in os.listdir('.'):
            if f.lower().endswith('.jar') and "apkeditor" in f.lower():
                ok(f"APKEditor found: {f}")
                return f
    except Exception:
        pass
    jars = glob.glob("APKEditor*.jar") + glob.glob("*APKEditor*.jar")
    if jars:
        ok(f"APKEditor found: {jars[0]}")
        return jars[0]
    
    try:
        spinner("Downloading latest APKEditor...", 2.0)
        api_url = "https://api.github.com/repos/REAndroid/APKEditor/releases/latest"
        with urllib.request.urlopen(api_url) as resp:
            data = json.load(resp)
        
        for asset in data.get("assets", []):
            if asset["name"].endswith(".jar") and "apkeditor" in asset["name"].lower():
                download_url = asset["browser_download_url"]
                filename = asset["name"]
                break
        else:
            download_url = "https://github.com/REAndroid/APKEditor/releases/latest/download/APKEditor.jar"
            filename = "APKEditor.jar"
        
        req = urllib.request.Request(download_url, headers={'User-Agent': 'flutter_patcher/1.0'})
        dest = os.path.join(MMK_FILES_DIR, filename)
        mmk_ensure_dirs()
        with urllib.request.urlopen(req) as resp, open(dest, 'wb') as f:
            shutil.copyfileobj(resp, f)
        ok(f"APKEditor successfully downloaded: {dest}")
        return dest
        
    except Exception as e:
        err(f"APKEditor download error: {e}")
        return None

def extract_arm64_folder_from_apk(apk_path, dest_parent='.'):
    """Extract arm64-v8a folder and libapp.so from APK"""
    if not os.path.exists(apk_path):
        raise FileNotFoundError(f"APK not found: {apk_path}")

    banner("EXTRACT NATIVE LIBS", "lib/arm64-v8a + libapp.so")
    spinner("Membuka APK & scan library...", 1.0)

    with zipfile.ZipFile(apk_path, 'r') as z:
        members = [m for m in z.namelist() if m.startswith('lib/arm64-v8a/')]
        if not members:
            raise RuntimeError("'lib/arm64-v8a/' folder not found in APK.")

        ok(f"Ditemukan {len(members)} file di lib/arm64-v8a/")
        tmpdir = tempfile.mkdtemp(prefix='apk_extract_')
        try:
            total = len([m for m in members if not m.endswith('/')])
            done = 0
            for m in members:
                if not m.endswith('/'):
                    z.extract(m, path=tmpdir)
                    done += 1
                    if total:
                        progress_bar(done, total, "extract")

            src_folder = os.path.join(tmpdir, 'lib', 'arm64-v8a')
            dst_folder = os.path.join(os.path.abspath(dest_parent), 'arm64-v8a')

            if os.path.exists(dst_folder):
                spinner("Menghapus arm64-v8a lama...", 0.6)
                shutil.rmtree(dst_folder)
            shutil.move(src_folder, dst_folder)
            ok(f"lib/arm64-v8a → {dst_folder}")

            libso = os.path.join(dst_folder, 'libapp.so')
            if os.path.exists(libso):
                dst_so = os.path.join(os.path.abspath(dest_parent), 'libapp.so')
                if os.path.exists(dst_so):
                    os.remove(dst_so)
                spinner("Copy libapp.so...", 0.5)
                shutil.copy(libso, dst_so)
                size = human_size(os.path.getsize(dst_so))
                ok(f"libapp.so siap ({size})")
            else:
                warn("libapp.so tidak ditemukan di arm64-v8a")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

def ensure_blutter_termux():
    """
    Pastikan Blutter Termux tersedia di ~/blutter-termux (seperti script original).
    - Clone dari AbhiTheModder/blutter-termux jika belum ada
    - Patch std::format → fmt::format
    """
    home = os.path.expanduser("~")
    blutter_dir = os.path.join(home, "blutter-termux")
    blutter_py = os.path.join(blutter_dir, "blutter.py")

    if os.path.exists(blutter_py):
        ok(f"Blutter Termux siap: {blutter_dir}")
        return blutter_dir

    banner("INSTALL BLUTTER TERMUX", "clone + patch fmt::format")
    spinner("Cloning AbhiTheModder/blutter-termux ...", 1.5)

    try:
        # hapus folder setengah jadi
        if os.path.isdir(blutter_dir) and not os.path.exists(blutter_py):
            shutil.rmtree(blutter_dir, ignore_errors=True)

        subprocess.run(
            ["git", "clone", "--depth", "1",
             "https://github.com/AbhiTheModder/blutter-termux.git", blutter_dir],
            check=True,
        )
        ok("Repo di-clone")

        spinner("Patch std::format → fmt::format ...", 1.0)
        subprocess.run(
            ["find", blutter_dir, "-type", "f",
             "-exec", "sed", "-i", "s/std::format/fmt::format/g", "{}", "+"],
            check=False,
        )
        ok("Patch fmt selesai")

        if not os.path.exists(blutter_py):
            err("blutter.py tidak ditemukan setelah clone")
            return None

        ok(f"Blutter Termux terpasang di {blutter_dir}")
        return blutter_dir
    except Exception as e:
        err(f"Gagal install Blutter: {e}")
        return None


def _pretty_blutter_line(line: str) -> str:
    """Format setiap baris output Blutter agar tampil keren."""
    s = line.rstrip("\n\r")
    if not s.strip():
        return ""

    low = s.lower().strip()

    # ── status sukses / update ──
    if "already up to date" in low:
        return f"  {C.GREEN}✓{C.RESET}  Already up to date"
    if low.startswith("dart version"):
        # Dart version: 3.11.5, Snapshot: ..., Target: android arm64
        return f"  {C.CYAN}◆{C.RESET}  {C.BOLD}{s.strip()}{C.RESET}"
    if low.startswith("flags:"):
        return f"  {C.DIM}│   {s.strip()}{C.RESET}"
    if "null_safety" in low or "null-safety" in low:
        return f"  {C.DIM}│   {s.strip()}{C.RESET}"
    if "libapp is loaded" in low:
        return f"  {C.GREEN}✓{C.RESET}  {s.strip()}"
    if "dart heap" in low:
        return f"  {C.DIM}│   {s.strip()}{C.RESET}"

    # ── tahap utama ──
    if "analyzing the application" in low:
        return f"\n  {C.MAGENTA}┌─ ANALYZE{C.RESET}\n  {C.MAGENTA}│{C.RESET}  {C.BOLD}Analyzing the application...{C.RESET}"
    if "dumping object pool" in low:
        return f"\n  {C.MAGENTA}┌─ DUMP{C.RESET}\n  {C.MAGENTA}│{C.RESET}  {C.BOLD}Dumping Object Pool...{C.RESET}"
    if "generating application assemblies" in low:
        return f"\n  {C.MAGENTA}┌─ ASM{C.RESET}\n  {C.MAGENTA}│{C.RESET}  {C.BOLD}Generating application assemblies...{C.RESET}"
    if "generating radare2 script" in low:
        return f"  {C.GREEN}✓{C.RESET}  Generating radare2 script"
    if "generating ida script" in low:
        return f"  {C.GREEN}✓{C.RESET}  Generating IDA script"
    if "generating frida script" in low:
        return f"  {C.GREEN}✓{C.RESET}  Generating Frida script"

    # ── error / analysis warning ──
    if "analysis error" in low:
        return f"  {C.YELLOW}⚠{C.RESET}  {C.YELLOW}{s.strip()[:90]}{C.RESET}"
    if s.strip().startswith("0x") or s.strip().startswith("* 0x"):
        return f"  {C.DIM}│     {s.strip()}{C.RESET}"
    if "error" in low or "failed" in low or "fatal" in low:
        return f"  {C.RED}✗{C.RESET}  {s.strip()[:100]}"

    # ── git / compile noise ──
    if "cloning" in low or "checking out" in low:
        return f"  {C.CYAN}↓{C.RESET}  {s.strip()[:80]}"
    if "compiling" in low or "building" in low or "cmake" in low:
        return f"  {C.CYAN}⚙{C.RESET}  {s.strip()[:80]}"
    if "sparse-checkout" in low:
        return f"  {C.CYAN}↓{C.RESET}  git sparse-checkout..."

    # default
    return f"  {C.DIM}│  {s.strip()[:90]}{C.RESET}"


def run_blutter(filename, apk_dir):
    """
    Jalankan Blutter seperti script original (Termux ~/blutter-termux)
    + semua output di-format biar keren.
    """
    banner("BLUTTER ENGINE", "Dart AOT dump → asm + pp.txt")

    blutter_dir = ensure_blutter_termux()
    if not blutter_dir:
        raise RuntimeError(
            "Blutter Termux tidak tersedia. "
            "Install manual: git clone https://github.com/AbhiTheModder/blutter-termux.git ~/blutter-termux"
        )

    extracted_path = os.path.join(apk_dir, "arm64-v8a")
    if not os.path.exists(extracted_path):
        os.makedirs(extracted_path, exist_ok=True)

    # Blutter butuh libapp.so di dalam folder input
    libapp_in = os.path.join(extracted_path, "libapp.so")
    if not os.path.isfile(libapp_in):
        # fallback: copy dari apk_dir/libapp.so jika ada
        alt = os.path.join(apk_dir, "libapp.so")
        if os.path.isfile(alt):
            spinner("Copy libapp.so → arm64-v8a/...", 0.5)
            shutil.copy2(alt, libapp_in)
            ok(f"libapp.so → {libapp_in}")
        else:
            raise RuntimeError(
                f"libapp.so tidak ditemukan di {extracted_path}\n"
                "  Extract APK dulu atau letakkan libapp.so di arm64-v8a/"
            )
    else:
        ok(f"libapp.so OK ({human_size(os.path.getsize(libapp_in))})")

    out_dir = os.path.join(blutter_dir, f"out_dir_{filename}")
    info(f"Blutter : {blutter_dir}")
    info(f"Input   : {extracted_path}")
    info(f"Output  : {out_dir}")

    if os.path.isdir(out_dir):
        spinner("Membersihkan out_dir lama...", 0.6)
        shutil.rmtree(out_dir, ignore_errors=True)

    cmd = ["python3", "blutter.py", extracted_path, out_dir]
    print()
    print(f"  {C.CYAN}▶{C.RESET}  blutter.py  {C.DIM}arm64-v8a → out_dir_{filename}{C.RESET}")
    print(f"  {C.DIM}   first run bisa lama (download + compile Dart VM){C.RESET}")
    print(f"  {C.BLUE}{'─' * 50}{C.RESET}")

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    # Stream stdout+stderr baris demi baris, format keren
    proc = subprocess.Popen(
        cmd,
        cwd=blutter_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    try:
        for raw in proc.stdout:
            pretty = _pretty_blutter_line(raw)
            if pretty:
                print(pretty, flush=True)
    except KeyboardInterrupt:
        proc.kill()
        raise

    proc.wait()
    print(f"  {C.BLUE}{'─' * 50}{C.RESET}")

    if proc.returncode != 0:
        err(f"Blutter exit code {proc.returncode}")
        dartsdk = os.path.join(blutter_dir, "dartsdk")
        if os.path.isdir(dartsdk):
            warn("Folder dartsdk ada — mungkin download/compile gagal")
            info("Coba: rm -rf ~/blutter-termux/dartsdk ~/blutter-termux/build")
            info("Lalu jalankan ulang (butuh jaringan stabil)")
        raise RuntimeError(
            f"Blutter gagal (code {proc.returncode}). "
            "Pastikan jaringan OK dan git/cmake/g++ terpasang."
        )

    asm_folder = os.path.join(out_dir, "asm")
    if os.path.exists(asm_folder):
        n_dart = sum(1 for _, _, fs in os.walk(asm_folder) for f in fs if f.endswith(".dart"))
        ok(f"asm/ siap — {n_dart} file .dart")
    else:
        warn("Folder asm/ tidak dibuat — Blutter mungkin belum selesai compile Dart VM")

    pp_source = os.path.join(out_dir, "pp.txt")
    pp_dest = os.path.join(apk_dir, "pp.txt")
    if os.path.exists(pp_source):
        spinner("Copy pp.txt...", 0.4)
        shutil.copy(pp_source, pp_dest)
        ok(f"pp.txt → {pp_dest}")
    else:
        warn("pp.txt tidak ditemukan")

    return out_dir

def replace_lib_in_apk(apk_path, patched_lib):
    """Replace libapp.so in APK with patched version"""
    banner("REPACK APK", "inject patched libapp.so")
    spinner("Menulis ulang ZIP entries...", 1.0)

    tmp_apk = apk_path + ".tmp"
    replaced = False
    with zipfile.ZipFile(apk_path, 'r') as zin, zipfile.ZipFile(tmp_apk, 'w') as zout:
        items = zin.infolist()
        for i, item in enumerate(items, 1):
            if item.filename == "lib/arm64-v8a/libapp.so":
                zout.write(patched_lib, item.filename)
                replaced = True
                print(f"  {C.GREEN}│  ★ replaced {item.filename}{C.RESET}")
            else:
                zout.writestr(item, zin.read(item.filename))
            if i % 50 == 0 or i == len(items):
                progress_bar(i, len(items), "repack")

    os.replace(tmp_apk, apk_path)
    if replaced:
        ok(f"libapp.so injected → {os.path.basename(apk_path)}")
    else:
        warn("lib/arm64-v8a/libapp.so tidak ketemu di APK (tidak diganti)")

def cleanup_workspace(apk_dir):
    """Clean up temporary files and folders"""
    banner("CLEANUP", "hapus file sementara")

    for folder in ['arm64-v8a']:
        folder_path = os.path.join(apk_dir, folder)
        if os.path.exists(folder_path):
            spinner(f"Hapus folder {folder}/...", 0.5)
            shutil.rmtree(folder_path, ignore_errors=True)
            ok(f"Folder dihapus: {folder}/")

    for file in ['libapp.so']:
        file_path = os.path.join(apk_dir, file)
        if os.path.exists(file_path):
            spinner(f"Hapus {file}...", 0.3)
            os.remove(file_path)
            ok(f"File dihapus: {file}")


def find_related_functions(lib_path, pp_address, timeout=12):
    print(f"Searching for related functions for {pp_address} using pptool...\n")
    output = ""

    try:
        proc = subprocess.run(["pptool", lib_path, pp_address],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, timeout=timeout)
        output = proc.stdout or ""
    except Exception:
        pass

    if not output.strip():
        try:
            proc = subprocess.run(["r2", "-w", lib_path, "-c",
                                   f'!pptool {lib_path} {pp_address}; q'],
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, timeout=timeout)
            output = proc.stdout or ""
        except Exception:
            pass

    if not output.strip():
        print("No pptool output found.")
        return []

    ansi_re = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')
    clean = ansi_re.sub("", output)
    lines = [re.sub(r'[ \t]+', ' ', ln).strip() for ln in clean.splitlines()]

    triple_re = re.compile(r'(0x[0-9a-fA-F]+)\s+(0x[0-9a-fA-F]+)\s+(0x[0-9a-fA-F]+)')
    matches = [(m.group(1), m.group(3)) for ln in lines if (m := triple_re.search(ln))]

    if not matches:
        for ln in lines:
            toks = re.findall(r'0x[0-9a-fA-F]+', ln)
            if len(toks) >= 3:
                matches.append((toks[0], toks[-1]))

    if not matches:
        print("No function-offset pairs found.")
        return []

    seen, functions = set(), []
    for func_addr, offset in matches:
        key = (func_addr.lower(), offset.lower())
        if key not in seen:
            seen.add(key)
            functions.append((func_addr, offset))

    print("Related functions found:\n")
    for i, (func_addr, offset) in enumerate(functions, start=1):
        print(f" {i}. function_address = {func_addr} | offset_value = {offset}")
    print("\nRelated functions search completed.")

    return functions

def analyze_function_with_r2_commands(libso_path, func_addr):
    try:
        r2 = r2pipe.open(libso_path, flags=["-2"])
        
        print(f"  → s {func_addr}")
        r2.cmd(f"s {func_addr}")
        
        print(f"  → aF")
        r2.cmd("aF")
        
        print(f"  → pdr")
        disasm = r2.cmd("pdr")
        
        r2.quit()
        return disasm
    except Exception as e:
        print(f"R2 command analysis error: {e}")
        return ""

def patch_true_functions(libso_path, related_funcs, indices):
    """PP PATCHING: FALSE patch mode (0x20 → 0x30)"""
    if not related_funcs:
        print("No related functions provided.")
        return {}

    print("\n" + "="*60)
    print("✅ FALSE PATCH MODE (0x20 → 0x30)")
    print("="*60)
    print("🔍 Searching: add x[0-30], x22, 0x20")
    print("🔄 Replacing: add x[0-30], x22, 0x30")
    print("="*60 + "\n")
  
    patterns = [
        r"add\s+(x([0-9]|[12][0-9]|30)),\s*x22,\s*0x20",
        r"add\s+(x([0-9]|[12][0-9]|30)),\s*x22,\s*#?0x20"
    ]
    
    results = {}

    try:
        for i in indices:
            func_addr, offset = related_funcs[i-1]
            print(f"\n➡️  Checking function #{i} for FALSE patch @ {func_addr} (offset {offset})")
            
            print("  Executing R2 commands...")
            disasm = analyze_function_with_r2_commands(libso_path, func_addr)
            
            if not disasm:
                print("  ⚠️  Could not get disassembly from R2 commands")
                results[i] = (func_addr, offset, False, None, None, "TRUE_PATCH")
                continue
            
            patched = False
            patched_at = None
            matched_register = None
            matched_instr = None
            
            for pattern in patterns:
                for line in disasm.splitlines():
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match and "0x20" in line:
                        matched_register = match.group(1)
                        addr_match = re.search(r"(0x[0-9a-fA-F]+)", line)
                        instr_addr = addr_match.group(1) if addr_match else func_addr
                        matched_instr = line.strip()
                        
                        print(f"✅ TRUE pattern found: {matched_instr}")
                        print(f"   Address: {instr_addr}")
                        print(f"   Register: {matched_register}")
                        
                        try:
                            r2 = r2pipe.open(libso_path, flags=["-w", "-2"])
                            r2.cmd(f"s {instr_addr}")
                            r2.cmd(f"wa add {matched_register}, x22, 0x30")
                            r2.quit()
                            
                            print(f"   ↪️  Patched to 'add {matched_register}, x22, 0x30' (true → false)")
                            
                            patched = True
                            patched_at = instr_addr
                            break
                        except Exception as e:
                            print(f"   ❌ Patching error: {e}")
                if patched:
                    break

            results[i] = (func_addr, offset, patched, patched_at, matched_register, "TRUE_PATCH")
            if patched:
                print(f"🎯 Function #{i} FALSE patched at {patched_at}.")
            else:
                print(f"⚠️ Function #{i}: No target found for FALSE patch.")
                
                print("\n📄 pdr output (first 3 lines):")
                for j, line in enumerate(disasm.splitlines()[:3]):
                    print(f"  {j:3d}: {line}")

    except Exception as e:
        print(f"❌ FALSE patching error: {e}")

    return results

def patch_false_functions(libso_path, related_funcs, indices):
    """PP PATCHING: TRUE patch mode (0x30 → 0x20)"""
    if not related_funcs:
        print("No related functions provided.")
        return {}

    print("\n" + "="*60)
    print("❌ TRUE PATCH MODE (0x30 → 0x20)")
    print("="*60)
    print("🔍 Searching: add x[0-30], x22, 0x30")
    print("🔄 Replacing: add x[0-30], x22, 0x20")
    print("="*60 + "\n")
  
    patterns = [
        r"add\s+(x([0-9]|[12][0-9]|30)),\s*x22,\s*0x30",
        r"add\s+(x([0-9]|[12][0-9]|30)),\s*x22,\s*#?0x30"
    ]
    
    results = {}

    try:
        for i in indices:
            func_addr, offset = related_funcs[i-1]
            print(f"\n➡️  Checking function #{i} for TRUE patch @ {func_addr} (offset {offset})")
            
            print("  Executing R2 commands...")
            disasm = analyze_function_with_r2_commands(libso_path, func_addr)
            
            if not disasm:
                print("  ⚠️  Could not get disassembly from R2 commands")
                results[i] = (func_addr, offset, False, None, None, "FALSE_PATCH")
                continue
            
            patched = False
            patched_at = None
            matched_register = None
            matched_instr = None
            
            for pattern in patterns:
                for line in disasm.splitlines():
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match and "0x30" in line:
                        matched_register = match.group(1)
                        addr_match = re.search(r"(0x[0-9a-fA-F]+)", line)
                        instr_addr = addr_match.group(1) if addr_match else func_addr
                        matched_instr = line.strip()
                        
                        print(f"✅ FALSE pattern found: {matched_instr}")
                        print(f"   Address: {instr_addr}")
                        print(f"   Register: {matched_register}")
                        
                        try:
                            r2 = r2pipe.open(libso_path, flags=["-w", "-2"])
                            r2.cmd(f"s {instr_addr}")
                            r2.cmd(f"wa add {matched_register}, x22, 0x20")
                            r2.quit()
                            
                            print(f"   ↪️  Patched to 'add {matched_register}, x22, 0x20' (false → true)")
                            
                            patched = True
                            patched_at = instr_addr
                            break
                        except Exception as e:
                            print(f"   ❌ Patching error: {e}")
                if patched:
                    break

            results[i] = (func_addr, offset, patched, patched_at, matched_register, "FALSE_PATCH")
            if patched:
                print(f"🎯 Function #{i} TRUE patched at {patched_at}.")
            else:
                print(f"⚠️ Function #{i}: No target found for TRUE patch.")
                
                print("\n📄 pdr output (first 3 lines):")
                for j, line in enumerate(disasm.splitlines()[:3]):
                    print(f"  {j:3d}: {line}")

    except Exception as e:
        print(f"❌ TRUE patching error: {e}")

    return results


def _asm_extract_keyword(text):
    """Ambil nama method/keyword premium dari teks match."""
    if not text:
        return "-"
    # prioritas: identifier yang berkaitan premium/vip/pro/subs
    patterns = [
        r'\b((?:is|get|has|set|check)?[A-Za-z0-9_]*(?:Premium|ProUser|ProVersion|isPro|IsPro|Vip|VIP|SVIP|Svip|Subscription|Subscribe|Subscribed|Purchased|Purchase|LifetimeTime|lifetime|NoAds|AdFree|Gold|Elite|Paid|Unlocked|entitlement)[A-Za-z0-9_]*)\b',
        r'\b(SVIP|SvipState|CustomerInfo|entitlementinfo|dailyAdKey|pro_access_life_time|premiumstatus|Premium_is_active)\b',
        r'\b([A-Za-z_][A-Za-z0-9_]{2,40})\s*\([^)]*\)\s*(?:async\s*)?\{',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            kw = m.group(1).strip()
            if len(kw) >= 2 and kw.lower() not in ("true", "false", "null", "this", "void", "async"):
                return kw[:40]
    # fallback: potong baris pertama yang ada huruf
    for line in str(text).splitlines():
        line = line.strip()
        if line and re.search(r'[A-Za-z]{3,}', line):
            return re.sub(r'\s+', ' ', line)[:40]
    return "-"


def search_asm_folder(asm_folder):
    """Search for regex patterns in .dart files within asm folder"""
    banner("SEARCHING ASM FOLDER", "Regex pattern hunter")

    all_matches = []

    if not os.path.exists(asm_folder):
        err(f"asm folder not found: {asm_folder}")
        return all_matches

    dart_files = []
    for root, dirs, files in os.walk(asm_folder):
        for file in files:
            if file.endswith('.dart'):
                dart_files.append(os.path.join(root, file))

    ok(f"Found {len(dart_files)} .dart files")

    for i, dart_file in enumerate(dart_files, 1):
        try:
            with open(dart_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            for regex_pattern in ASM_REGEX_PATTERNS:
                matches = re.finditer(regex_pattern, content, re.IGNORECASE)
                for match in matches:
                    addr_match = re.search(
                        r'// \*\* addr: (0x[0-9a-fA-F]+)',
                        content[max(0, match.start() - 200):match.end()],
                    )
                    if addr_match:
                        address = addr_match.group(1)
                        mt = match.group()
                        if len(mt) > 400:
                            mt = mt[:400]
                        kw = _asm_extract_keyword(mt)
                        all_matches.append({
                            'address': address,
                            'context': mt,
                            'file': os.path.relpath(dart_file, asm_folder),
                            'match_text': mt,
                            'keyword': kw,
                        })
                        if len(all_matches) % 10 == 0:
                            print(f"  Found {len(all_matches)} matches so far...")

        except Exception as e:
            err(f"Error reading {os.path.basename(dart_file)}: {e}")

        if i % 50 == 0 or i == len(dart_files):
            progress_bar(i, len(dart_files), "Scanning .dart")

    ok(f"Total matches found: {len(all_matches)}")
    return all_matches


def create_smngn_file(matches, output_file="smngn.txt"):
    """Create smngn.txt file with all matches"""
    info(f"Creating {output_file}...")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("SMNGN REGEX MATCHES\n")
        f.write("=" * 60 + "\n\n")

        for i, match in enumerate(matches, 1):
            kw = match.get('keyword') or _asm_extract_keyword(match.get('match_text') or match.get('context') or '')
            f.write(f"MATCH #{i}\n")
            f.write(f"Address: {match['address']}\n")
            f.write(f"Keyword: {kw}\n")
            f.write(f"File: {match['file']}\n")
            f.write(f"Context:\n{match['context']}\n")
            f.write(f"Match Text:\n{match['match_text']}\n")
            f.write("-" * 60 + "\n\n")

    ok(f"{output_file} created with {len(matches)} matches")
    return output_file


def extract_false_addresses_from_smngn(smngn_file):
    """
    Extract false addresses from smngn.txt.
    Return list of dict: {address, keyword, line}
    Keyword diambil dari blok MATCH terdekat (Keyword: ... / match text).
    """
    banner("EXTRACT FALSE ADDRESSES", os.path.basename(smngn_file))

    results = []
    seen = set()

    if not os.path.exists(smngn_file):
        err(f"{smngn_file} not found")
        return results

    try:
        with open(smngn_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # pecah per blok MATCH
        blocks = re.split(r'(?=MATCH #\d+)', content)
        addr_to_kw = {}
        for block in blocks:
            if not block.strip():
                continue
            kw_m = re.search(r'^Keyword:\s*(.+)$', block, re.M)
            kw = kw_m.group(1).strip() if kw_m else ""
            if not kw or kw == "-":
                kw = _asm_extract_keyword(block)
            for pattern in ASM_FALSE_PATTERNS:
                for match in re.finditer(pattern, block, re.IGNORECASE):
                    address = match.group(1)
                    if address not in addr_to_kw:
                        addr_to_kw[address] = kw or "-"

        # fallback scan global jika blok kosong
        if not addr_to_kw:
            for pattern in ASM_FALSE_PATTERNS:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    address = match.group(1)
                    if address not in addr_to_kw:
                        # cari keyword di 800 char sebelum address
                        pos = match.start()
                        window = content[max(0, pos - 800):pos + 120]
                        addr_to_kw[address] = _asm_extract_keyword(window)

        for address, kw in addr_to_kw.items():
            if address in seen:
                continue
            seen.add(address)
            short_line = ""
            for line in content.splitlines():
                if address in line and 'false' in line.lower():
                    short_line = line.strip()
                    if len(short_line) > 70:
                        short_line = short_line[:67] + "..."
                    break
            print(
                f"  {C.YELLOW}◆{C.RESET} {C.CYAN}{address}{C.RESET}  "
                f"{C.GREEN}{kw}{C.RESET}  {C.DIM}{short_line}{C.RESET}"
            )
            results.append({"address": address, "keyword": kw or "-", "line": short_line})

        print()
        ok(f"Extracted {len(results)} false addresses")
        print()
        # simpan map untuk patcher
        extract_false_addresses_from_smngn.last_map = {
            x["address"]: x["keyword"] for x in results
        }
        return results

    except Exception as e:
        err(f"Error reading {smngn_file}: {e}")
        return []


def patch_false_addresses(libso_path, false_addresses, keyword_map=None):
    """ASM PATCHING: Patch false addresses (false → true) — cool UI"""
    # normalisasi: list str atau list dict
    entries = []
    for item in false_addresses or []:
        if isinstance(item, dict):
            entries.append((item.get("address"), item.get("keyword") or "-"))
        else:
            kw = (keyword_map or {}).get(str(item), "-")
            entries.append((str(item), kw))

    if not entries:
        warn("No false addresses to patch")
        return {}

    total = len(entries)
    banner("ASM BINARY PATCHER", f"false → true  •  {total} targets")
    print(f"  {C.DIM}Pattern : add xN, x22, 0x30  →  add xN, x22, 0x20{C.RESET}")
    print(f"  {C.DIM}Engine  : radare2  (wa write-assembly){C.RESET}")
    print()

    results = {}
    success_count = 0
    keyword_map = keyword_map or {}
    try:
        keyword_map.update(getattr(extract_false_addresses_from_smngn, "last_map", {}) or {})
    except Exception:
        pass

    for i, (address, kw) in enumerate(entries, 1):
        if not kw or kw == "-":
            kw = keyword_map.get(address, "-")
        pct = int((i / total) * 20)
        bar = "█" * pct + "░" * (20 - pct)
        print(f"  {C.CYAN}┌─[{i:02d}/{total:02d}]─ {bar}  {address}  {C.GREEN}{kw}{C.RESET}")

        try:
            r2 = r2pipe.open(libso_path, flags=["-w", "-2"])

            r2.cmd(f"s {address}")
            disasm = r2.cmd("pd1").strip()

            print(f"  {C.DIM}│  ORIG  {disasm}{C.RESET}")

            add_pattern = r"add\s+(x([0-9]|[12][0-9]|30)),\s*x22,\s*0x30"
            match = re.search(add_pattern, disasm, re.IGNORECASE)

            if match:
                matched_register = match.group(1)
                patch_cmd = f"wa add {matched_register}, x22, 0x20"
                r2.cmd(patch_cmd)

                r2.cmd(f"s {address}")
                verify = r2.cmd("pd1").strip()

                print(f"  {C.GREEN}│  PATCH {verify}{C.RESET}")
                print(f"  {C.GREEN}└─ ✓  {matched_register}  0x30 → 0x20  OK  ·  {kw}{C.RESET}")
                success_count += 1

                results[address] = {
                    'patched': True,
                    'original': disasm,
                    'patched_to': verify,
                    'register': matched_register,
                    'type': 'FALSE_TO_TRUE',
                    'keyword': kw,
                }
            else:
                print(f"  {C.YELLOW}│  SKIP  pola tidak cocok{C.RESET}")
                print(f"  {C.YELLOW}└─ ✗  {disasm[:60]}{C.RESET}")
                results[address] = {
                    'patched': False,
                    'reason': 'Not matching pattern',
                    'instruction': disasm,
                    'keyword': kw,
                }

            r2.quit()

        except Exception as e:
            print(f"  {C.RED}│  ERROR {e}{C.RESET}")
            print(f"  {C.RED}└─ ✗  gagal{C.RESET}")
            results[address] = {
                'patched': False,
                'reason': str(e),
                'keyword': kw,
            }

        print()

    # final summary box
    fail = total - success_count
    print(f"  {C.MAGENTA}╔{'═'*42}╗{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  {C.BOLD}ASM PATCH SUMMARY{C.RESET}{' '*24}{C.MAGENTA}║{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  {C.GREEN}✓ success : {success_count:>3}{C.RESET}{' '*26}{C.MAGENTA}║{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  {C.RED}✗ failed  : {fail:>3}{C.RESET}{' '*26}{C.MAGENTA}║{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  {C.CYAN}Σ total   : {total:>3}{C.RESET}{' '*26}{C.MAGENTA}║{C.RESET}")
    print(f"  {C.MAGENTA}╚{'═'*42}╝{C.RESET}")
    print()

    return results


def process_pp_patch(apk_path):
    """Process pp.txt based patching"""
    if not ENABLE_PP_PATCH:
        print("PP Patching disabled.")
        return apk_path, 0
    
    print("\n" + "="*60)
    print("PP.TXT BASED PATCHING")
    print("="*60)
    
    apk_dir = os.path.dirname(os.path.abspath(apk_path))
    if not apk_dir:
        apk_dir = "."
    
    print(f"TRUE Keywords: {KEYWORDS_TRUE}")
    print(f"FALSE Keywords: {KEYWORDS_FALSE}")
    
    
    pp_txt = os.path.join(apk_dir, "pp.txt")
    if not os.path.exists(pp_txt):
        print("pp.txt not found!")
        return apk_path, 0

    pp_addresses_true = []
    pp_addresses_false = []
    process_pp_patch._kw_true = []
    process_pp_patch._kw_false = []

    with open(pp_txt, "r", errors="ignore") as f:
        lines = f.readlines()

    if ENABLE_TRUE_PATCH:
        for kw in KEYWORDS_TRUE:
            found_for_kw = False
            for line in lines:
                if kw.lower() in line.lower():
                    m = re.search(r"\[pp\+(0x[0-9a-fA-F]+)\]", line)
                    if m:
                        pp_addr = m.group(1)
                        if pp_addr not in pp_addresses_true:
                            pp_addresses_true.append(pp_addr)
                            print(f"✓ Address found for TRUE '{kw}' → {pp_addr}")
                            found_for_kw = True
                            if not hasattr(process_pp_patch, "_kw_true"):
                                process_pp_patch._kw_true = []
                            process_pp_patch._kw_true.append((kw, pp_addr))
            if not found_for_kw:
                print(f"✗ No address found for TRUE '{kw}'")

    if ENABLE_FALSE_PATCH:
        for kw in KEYWORDS_FALSE:
            found_for_kw = False
            for line in lines:
                if kw.lower() in line.lower():
                    m = re.search(r"\[pp\+(0x[0-9a-fA-F]+)\]", line)
                    if m:
                        pp_addr = m.group(1)
                        if pp_addr not in pp_addresses_false:
                            pp_addresses_false.append(pp_addr)
                            print(f"✓ Address found for FALSE '{kw}' → {pp_addr}")
                            found_for_kw = True
                            if not hasattr(process_pp_patch, "_kw_false"):
                                process_pp_patch._kw_false = []
                            process_pp_patch._kw_false.append((kw, pp_addr))
            if not found_for_kw:
                print(f"✗ No address found for FALSE '{kw}'")

    libapp_path = os.path.join(apk_dir, "libapp.so")
    all_patch_results = {}

    if pp_addresses_true and ENABLE_TRUE_PATCH:
        print(f"\n{'='*60}")
        print(f"PP: STARTING TRUE PATCH PROCESS ({len(pp_addresses_true)} addresses)")
        print(f"{'='*60}")
        
        for idx, pp_address in enumerate(pp_addresses_true, 1):
            print(f"\n[{idx}/{len(pp_addresses_true)}] PP TRUE patch process for {pp_address}:")
            
            related_funcs = find_related_functions(libapp_path, pp_address)
            if related_funcs:
                max_index = len(related_funcs)
                indices = list(range(1, max_index + 1))
                patch_results = patch_true_functions(libapp_path, related_funcs, indices)
                
                for k, v in patch_results.items():
                    all_patch_results[f"TRUE_{pp_address}_{k}"] = v
            else:
                print(f"  ⚠️  No functions found for {pp_address}.")

    if pp_addresses_false and ENABLE_FALSE_PATCH:
        print(f"\n{'='*60}")
        print(f"PP: STARTING FALSE PATCH PROCESS ({len(pp_addresses_false)} addresses)")
        print(f"{'='*60}")
        
        for idx, pp_address in enumerate(pp_addresses_false, 1):
            print(f"\n[{idx}/{len(pp_addresses_false)}] PP FALSE patch process for {pp_address}:")
            
            related_funcs = find_related_functions(libapp_path, pp_address)
            if related_funcs:
                max_index = len(related_funcs)
                indices = list(range(1, max_index + 1))
                patch_results = patch_false_functions(libapp_path, related_funcs, indices)
                
                for k, v in patch_results.items():
                    all_patch_results[f"FALSE_{pp_address}_{k}"] = v
            else:
                print(f"  ⚠️  No functions found for {pp_address}.")

    successful_patches = sum(1 for info in all_patch_results.values() if info[2])
    print(f"\nPP PATCHING: {successful_patches} successful patches")

    # ── Tabel Hex | atur ke | keyword ──
    table_rows = []
    # dari keyword → address yang ditemukan
    for kw, addr in getattr(process_pp_patch, "_kw_true", []) or []:
        table_rows.append({"hex": addr, "set_to": "TRUE", "keyword": kw})
    for kw, addr in getattr(process_pp_patch, "_kw_false", []) or []:
        table_rows.append({"hex": addr, "set_to": "FALSE", "keyword": kw})
    # dari hasil patch biner
    for key, info in all_patch_results.items():
        try:
            # info: (func_addr, offset, patched, ...)
            func_addr = info[0] if isinstance(info, (list, tuple)) else info.get("addr", "-")
            patched = info[2] if isinstance(info, (list, tuple)) else info.get("patched", False)
            kind = "TRUE" if str(key).startswith("TRUE") else "FALSE"
            if patched:
                table_rows.append({
                    "hex": str(func_addr),
                    "set_to": kind,
                    "keyword": str(key)[:40],
                })
        except Exception:
            pass
    if table_rows:
        # dedupe by hex+keyword
        seen = set()
        uniq = []
        for r in table_rows:
            k = (r["hex"], r["keyword"])
            if k not in seen:
                seen.add(k)
                uniq.append(r)
        print_patch_table(uniq, title="Flutter PP · dart offsets")
        process_pp_patch.last_patches = uniq
    else:
        process_pp_patch.last_patches = []

    return apk_path, successful_patches

def process_asm_patch(apk_path, apk_dir, out_dir=None):
    """Process asm folder based patching. out_dir dari Blutter (opsional, hindari run 2x)."""
    if not ENABLE_ASM_PATCH:
        warn("ASM Patching disabled.")
        return 0
    
    banner("ASM FOLDER BASED PATCHING", "regex scan + binary patch")
    
    try:
        if not out_dir:
            base = os.path.splitext(os.path.basename(apk_path))[0]
            out_dir = run_blutter(base, apk_dir)
        
        if not out_dir:
            err("Blutter failed to create output directory")
            return 0
        
        
        asm_folder = os.path.join(out_dir, "asm")
        matches = search_asm_folder(asm_folder)
        
        if not matches:
            warn("No regex matches found in asm folder")
            return 0
        
 
        smngn_file = os.path.join(apk_dir, "smngn.txt")
        create_smngn_file(matches, smngn_file)
        
        
        false_addresses = extract_false_addresses_from_smngn(smngn_file)

        libapp_path = os.path.join(apk_dir, "libapp.so")

        if false_addresses:
            banner(f"ASM: PATCHING {len(false_addresses)} FALSE ADDRESSES", "false → true")

            patch_results = patch_false_addresses(libapp_path, false_addresses)

            successful_patches = sum(1 for info in patch_results.values() if info.get('patched', False))
            ok(f"ASM PATCHING: {successful_patches} successful patches")
            rows = []
            for addr, info in patch_results.items():
                if info.get("patched"):
                    rows.append({
                        "hex": str(addr),
                        "set_to": "TRUE",
                        "keyword": info.get("keyword") or info.get("register") or "-",
                    })
            process_asm_patch.last_patches = rows
            if rows:
                print_patch_table(rows, title="Flutter ASM · false→true")
            return successful_patches
        else:
            warn("ASM: No false addresses found to patch.")
            process_asm_patch.last_patches = []
            return 0

    except Exception as e:
        err(f"ASM patching error: {e}")
        try:
            if "mmk_history_add" in globals():
                mmk_history_add("flutter_asm", None, error=str(e), extra={"steps": "ASM error"})
        except Exception:
            pass
        process_asm_patch.last_patches = []
        return 0

def process_flutter_patch_combined(apk_path):
    """Combined flutter patching using both pp.txt and asm folder"""
    if not ENABLE_FLUTTER_PATCH:
        warn("Flutter patching disabled.")
        return apk_path
    
    banner("COMBINED FLUTTER PATCHING", "PP.TXT + ASM folder engine")
    info(f"PP Patching : {'ENABLED' if ENABLE_PP_PATCH else 'DISABLED'}")
    info(f"ASM Patching: {'ENABLED' if ENABLE_ASM_PATCH else 'DISABLED'}")
    
    apk_dir = os.path.dirname(os.path.abspath(apk_path))
    if not apk_dir:
        apk_dir = "."
    
    info(f"Working directory: {apk_dir}")
    
    total_successful_patches = 0
    
    try:
        extract_arm64_folder_from_apk(apk_path, apk_dir)
    except Exception as e:
        err(f"Extraction error: {e}")
        return apk_path
    
    # Blutter sekali saja
    base = os.path.splitext(os.path.basename(apk_path))[0]
    out_dir = run_blutter(base, apk_dir)
    
    if ENABLE_PP_PATCH:
        _, pp_patches = process_pp_patch(apk_path)
        total_successful_patches += pp_patches
    
    if ENABLE_ASM_PATCH:
        asm_patches = process_asm_patch(apk_path, apk_dir, out_dir=out_dir)
        total_successful_patches += asm_patches
    
   
    libapp_path = os.path.join(apk_dir, "libapp.so")
    
    final_apk = apk_path
    if total_successful_patches > 0:
        banner(f"TOTAL {total_successful_patches} PATCHES APPLIED", "Writing patched libapp.so back to APK")
        # simpan ke out/patched — jangan timpa file di app/
        dest = mmk_output("patched", f"{base}_flutter_patched.apk")
        try:
            shutil.copy2(apk_path, dest)
            final_apk = dest
        except Exception as e:
            warn(f"Copy ke out/patched gagal ({e}) — patch in-place")
            final_apk = apk_path
        spinner("Updating APK with patched libapp.so...", 1.0)
        replace_lib_in_apk(final_apk, libapp_path)
        ok("libapp.so replaced successfully")
        out_dir = os.path.dirname(os.path.abspath(final_apk))
        box_info([
            f"✔  Output    : {os.path.basename(final_apk)}",
            f"✔  Direktori : {out_dir}",
            f"✔  Patches   : {total_successful_patches}",
        ], title="FLUTTER OUTPUT")
    else:
        warn("NO PATCHES APPLIED")

    # kumpulkan patch table (PP + ASM)
    patches = list(getattr(process_pp_patch, "last_patches", None) or [])
    asm_last = getattr(process_asm_patch, "last_patches", None) or []
    patches.extend(asm_last)
    if patches:
        print_patch_table(patches, title="Flutter · semua offset")

    try:
        if "mmk_history_add" in globals():
            mmk_history_add(
                "flutter",
                final_apk,
                extra={
                    "ok": total_successful_patches,
                    "fail": 0 if total_successful_patches else 1,
                    "total": max(total_successful_patches, 1),
                    "steps": f"flutter · {total_successful_patches} patches",
                    "steps_detail": [f"PP+ASM patches: {total_successful_patches}"],
                    "patch_kind": "flutter",
                },
                patches=patches,
            )
    except Exception:
        pass

    cleanup_workspace(apk_dir)

    for file in ['pp.txt', 'smngn.txt']:
        file_path = os.path.join(apk_dir, file)
        if os.path.exists(file_path):
            os.remove(file_path)
            info(f"Temporary file removed: {os.path.basename(file_path)}")

    return final_apk


def find_apkeditor_jar():
    for f in os.listdir('.'):
        if f.lower().endswith('.jar') and "apkeditor" in f.lower():
            return f
    jars = glob.glob("APKEditor*.jar") + glob.glob("*APKEditor*.jar")
    return jars[0] if jars else None

def check_apkeditor_main():
    jar = find_apkeditor_jar()
    if not jar:
        err("APKEditor jar not found.")
        err("Please download APKEditor and place it in the same directory")
        sys.exit(1)
    ok(f"APKEditor jar found: {jar}")
    return jar

def run_command(komut, verbose=True, exit_on_error=True):
    try:
        result = subprocess.run(komut, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            if verbose:
                print(f"Command failed: {komut}\n{result.stderr}")
            if exit_on_error:
                sys.exit(1)
        return result.stdout.strip()
    except Exception as e:
        if verbose:
            print(f"Command error: {komut}\n{str(e)}")
        if exit_on_error:
            sys.exit(1)
        return ""

def decompile_apk(apk_yolu, cikti_klasoru, jar_file):
    """Decompile via APKEditor — progress bar, log disembunyikan."""
    jar = jar_file if os.path.isabs(str(jar_file)) else os.path.abspath(str(jar_file))
    cmd = ["java", "-jar", jar, "d", "-i", str(apk_yolu), "-o", str(cikti_klasoru), "-f"]
    if "run_java_quiet" in globals():
        rc = run_java_quiet(cmd, label="DECOMPILE")
        return rc == 0 and os.path.exists(cikti_klasoru)
    # fallback
    if "run_command" in globals():
        run_command(f'java -jar "{jar}" d -i "{apk_yolu}" -o "{cikti_klasoru}"', verbose=False)
    else:
        subprocess.call(cmd)
    return os.path.exists(cikti_klasoru)

def build_apk(kaynak_klasor, cikti_apk, jar_file):
    """Build via APKEditor — progress bar."""
    jar = jar_file if os.path.isabs(str(jar_file)) else os.path.abspath(str(jar_file))
    cmd = ["java", "-jar", jar, "b", "-i", str(kaynak_klasor), "-o", str(cikti_apk), "-f"]
    if "run_java_quiet" in globals():
        rc = run_java_quiet(cmd, label="BUILD")
        if rc == 0 and os.path.exists(cikti_apk):
            ok(f"APK built ({human_size(os.path.getsize(cikti_apk))})")
            return True
        return False
    if "run_command" in globals():
        run_command(f'java -jar "{jar}" b -i "{kaynak_klasor}" -o "{cikti_apk}"', verbose=False)
    else:
        subprocess.call(cmd)
    if os.path.exists(cikti_apk):
        ok(f"APK built ({human_size(os.path.getsize(cikti_apk))})")
        return True
    return False

MANIFEST_PATCHES = [
    (re.compile(r'<[^>]*\b(?:com\.pairip\.licensecheck|android\.vending\.CHECK_LICENSE)\b[^>]*/>'), 
     '<!-- License check disabled -->', "CHECK_LICENSE"),
    ("extractNativeLibs", lambda content: content.replace('android:extractNativeLibs="false"', ''))
]

def safe_regex_operation(pattern, replacement, content, description, file_path=""):
    try:
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        yeni_icerik = pattern.sub(replacement, content)
        return True, yeni_icerik, None if yeni_icerik != content else (True, content, f"Pattern not matched: {description}")
    except Exception as e:
        hata_mesaji = f"Regex error [{description}]: {str(e)}"
        if file_path:
            hata_mesaji += f" - File: {os.path.basename(file_path)}"
        return False, content, hata_mesaji

def safe_function_operation(func, content, description, file_path=""):
    try:
        yeni_icerik = func(content)
        return True, yeni_icerik, None
    except Exception as e:
        hata_mesaji = f"Function error [{description}]: {str(e)}"
        if file_path:
            hata_mesaji += f" - File: {os.path.basename(file_path)}"
        return False, content, hata_mesaji

def patch_android_manifest(decompile_klasoru):
    print("Patching AndroidManifest.xml...")
    manifest_yolu = os.path.join(decompile_klasoru, 'AndroidManifest.xml')
    if not os.path.exists(manifest_yolu):
        print("AndroidManifest.xml not found")
        return False
    
    try:
        with open(manifest_yolu, 'r', encoding='utf-8') as f:
            icerik = f.read()
        
        orijinal_icerik = icerik
        
        if not MANIFEST_PATCHES:
            print("No manifest patches defined")
            return True
        
        for patch in MANIFEST_PATCHES:
            if len(patch) == 3:
                pattern, replacement, aciklama = patch
                if isinstance(pattern, str):
                    pattern = re.compile(pattern)
                basarili, yeni_icerik, hata_mesaji = safe_regex_operation(pattern, replacement, icerik, aciklama, manifest_yolu)
                if not basarili:
                    print(f"Manifest patch error: {hata_mesaji}")
                    continue
                if yeni_icerik != icerik:
                    icerik = yeni_icerik
                    print(f"Applied (regex): {aciklama}")
            
            elif len(patch) == 2:
                aciklama, patch_func = patch
                basarili, yeni_icerik, hata_mesaji = safe_function_operation(patch_func, icerik, aciklama, manifest_yolu)
                if not basarili:
                    print(f"Manifest patch error: {hata_mesaji}")
                    continue
                if yeni_icerik != icerik:
                    icerik = yeni_icerik
                    print(f"Applied (function): {aciklama}")
        
        if icerik != orijinal_icerik:
            with open(manifest_yolu, 'w', encoding='utf-8') as f:
                f.write(icerik)
            print("AndroidManifest.xml successfully patched")
            return True
        else:
            print("No changes made to AndroidManifest.xml")
            return True
            
    except Exception as e:
        print(f"Failed to patch AndroidManifest.xml: {e}")
        return False

def process_manifest_patcher(apk_yolu, jar_file):
    if not os.path.exists(apk_yolu):
        print(f"APK file not found: {apk_yolu}")
        return False

    orijinal_klasor = os.getcwd()
    apk_abs_yolu = os.path.abspath(apk_yolu)
    jar_abs_yolu = os.path.join(orijinal_klasor, jar_file)
    
    base_name = os.path.splitext(os.path.basename(apk_yolu))[0]
    output_apk = f"{base_name}-patched.apk"
    output_abs_yolu = os.path.join(orijinal_klasor, output_apk)
    
    work_dir = os.path.expanduser("~/apk_patch_work")
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir, ignore_errors=True)
    os.makedirs(work_dir, exist_ok=True)
    
    try:
        os.chdir(work_dir)
        print("Copying files to working directory...")
        shutil.copy2(apk_abs_yolu, "input.apk")
        shutil.copy2(jar_abs_yolu, jar_file)
        
        decompile_dir = "decompiled_app"
        print("Step 1/2: Decompiling APK")
        baslangic_zamani = time.time()
        if not decompile_apk("input.apk", decompile_dir, jar_file):
            return False
        print(f"Decompile completed in {time.time() - baslangic_zamani:.1f} seconds")
        
        print("Step 2/2: Patching AndroidManifest.xml")
        baslangic_zamani = time.time()
        if not patch_android_manifest(decompile_dir):
            print("Failed to patch AndroidManifest.xml")
            return False
        print(f"AndroidManifest.xml patched in {time.time() - baslangic_zamani:.1f} seconds")
        
        print("Step 3/3: Building patched APK")
        baslangic_zamani = time.time()
        if not build_apk(decompile_dir, "output.apk", jar_file):
            return False
        print(f"Building completed in {time.time() - baslangic_zamani:.1f} seconds")
        
        if os.path.exists("output.apk"):
            shutil.move("output.apk", output_abs_yolu)
            dosya_boyutu = os.path.getsize(output_abs_yolu) / (1024 * 1024)
            print(f"Final APK: {output_apk} ({dosya_boyutu:.2f} MB)")
            
            if os.path.exists(apk_abs_yolu):
                os.remove(apk_abs_yolu)
                print(f"Deleted previous APK: {os.path.basename(apk_abs_yolu)}")
            
            return True
        else:
            print("Output APK not found")
            return False
            
    except Exception as e:
        print(f"Processing error: {e}")
        return False
    finally:
        os.chdir(orijinal_klasor)
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir, ignore_errors=True)


def ensure_apkeditor():
    jar = find_apkeditor_jar()
    if jar:
        print(f"APKEditor jar found: {jar}")
        return jar
    name, url = get_latest_apkeditor_url()
    print("APKEditor jar not found. Downloading latest version...")
    download_file(url, name)
    return name

def download_file(url, outname):
    print(f"Downloading: {url}")
    req = urllib.request.Request(url, headers={'User-Agent': 'flutter_patcher/1.0'})
    with urllib.request.urlopen(req) as resp, open(outname, 'wb') as f:
        shutil.copyfileobj(resp, f)
    print("Download completed.")

def get_latest_apkeditor_url():
    api_url = "https://api.github.com/repos/REAndroid/APKEditor/releases/latest"
    try:
        with urllib.request.urlopen(api_url) as resp:
            data = json.load(resp)
        for asset in data.get("assets", []):
            if asset["name"].endswith(".jar") and "apkeditor" in asset["name"].lower():
                return asset["name"], asset["browser_download_url"]
    except Exception:
        pass
    return "APKEditor.jar", "https://github.com/REAndroid/APKEditor/releases/latest/download/APKEditor.jar"

def has_java():
    return shutil.which("java") is not None

def run_merge(jarfile, apks, apk):
    cmd = ["java", "-jar", jarfile, "m", "-i", apks, "-o", apk]
    print("Merging split APKs...")
    return subprocess.call(cmd)

def auto_clean_splitfolder(base_name):
    folder = os.path.abspath(base_name)
    if os.path.isdir(folder):
        try:
            shutil.rmtree(folder)
            print(f"Split folder auto-cleaned: {folder}")
        except Exception as e:
            print(f"Warning: {folder} could not be removed: {e}")


def flutter_main():
    animate_startup()

    # Status panel
    print(f"\n  {C.CYAN}▸ Flutter Patch   :{C.RESET} {C.GREEN if ENABLE_FLUTTER_PATCH else C.RED}{'ENABLED' if ENABLE_FLUTTER_PATCH else 'DISABLED'}{C.RESET}")
    print(f"  {C.CYAN}▸ Manifest Patch  :{C.RESET} {C.GREEN if ENABLE_MANIFEST_PATCH else C.RED}{'ENABLED' if ENABLE_MANIFEST_PATCH else 'DISABLED'}{C.RESET}")
    print(f"  {C.CYAN}▸ PP Patching     :{C.RESET} {C.GREEN if ENABLE_PP_PATCH else C.RED}{'ENABLED' if ENABLE_PP_PATCH else 'DISABLED'}{C.RESET}")
    print(f"  {C.CYAN}▸ ASM Patching    :{C.RESET} {C.GREEN if ENABLE_ASM_PATCH else C.RED}{'ENABLED' if ENABLE_ASM_PATCH else 'DISABLED'}{C.RESET}")
    print(f"  {C.CYAN}▸ TRUE Patch      :{C.RESET} {C.GREEN if ENABLE_TRUE_PATCH else C.RED}{'ENABLED' if ENABLE_TRUE_PATCH else 'DISABLED'}{C.RESET}")
    print(f"  {C.CYAN}▸ FALSE Patch     :{C.RESET} {C.GREEN if ENABLE_FALSE_PATCH else C.RED}{'ENABLED' if ENABLE_FALSE_PATCH else 'DISABLED'}{C.RESET}")
    print(f"  {C.DIM}▸ ASM Patterns    : {len(ASM_REGEX_PATTERNS)} regex  |  Method: PP.TXT + ASM folder{C.RESET}")

    if ENABLE_AUTO_INSTALL:
        banner("AUTO INSTALLATION MODE ACTIVE")
        if not run_auto_installation():
            warn("Auto installation failed. Manual installation may be required.")
            input(f"\n{C.YELLOW}Press ENTER to continue...{C.RESET}")

    # ── Scan for target files (app/ + /home/app + cwd) ─────────
    candidates = mmk_list_apks((".apk", ".apks", ".xapk"))

    if not candidates:
        err(f"Tidak ada APK/APKS di: {MMK_APP_DIR}")
        info("Letakkan file di folder app/ lalu jalankan ulang")
        return

    # Beautiful SELECT TARGET menu
    selected = select_target(candidates, title="SELECT TARGET  •  APK / APKS")
    if selected is None:
        info("Dibatalkan oleh user.")
        return

    apk = None
    apks = None
    if selected.lower().endswith('.apks'):
        apks = selected
    else:
        apk = selected

    apk_dir = os.path.dirname(selected) or "."
    info(f"Working directory: {apk_dir}")

    # ── Merge APKS if needed ───────────────────────────────────
    if apks:
        if not has_java():
            err("Java not found — Termux: pkg install openjdk-17")
            return

        jar = ensure_apkeditor()
        outfile = apks.replace(".apks", ".apk")

        banner("MERGING SPLIT APKS", os.path.basename(apks))
        spinner(f"Merging → {os.path.basename(outfile)}...", 1.5)
        if run_merge(jar, apks, outfile) != 0:
            err("APKS merge failed.")
            return

        ok("APKS successfully merged to APK.")
        auto_clean_splitfolder(os.path.splitext(apks)[0])
        apk = outfile

    ok(f"Target APK: {os.path.basename(apk)}")

    # ── Flutter patch ──────────────────────────────────────────
    if ENABLE_FLUTTER_PATCH:
        apk = process_flutter_patch_combined(apk)
    else:
        warn("Flutter Patching Disabled")

    # ── Manifest patch ─────────────────────────────────────────
    if ENABLE_MANIFEST_PATCH:
        banner("MANIFEST PATCHING PROCESS", "AndroidManifest.xml surgery")
        
        jar_file = check_apkeditor_main()
        baslangic_zamani = time.time()
        
        if process_manifest_patcher(apk, jar_file):
            total_time = time.time() - baslangic_zamani
            ok(f"Manifest patching completed in {total_time:.1f}s")
        else:
            err("Manifest patching failed")
    else:
        warn("Manifest Patching Disabled")

    # ── Finish ─────────────────────────────────────────────────
    print()
    print(f"{C.MAGENTA}╔{'═'*62}╗{C.RESET}")
    print(f"{C.MAGENTA}║{C.RESET}{C.BOLD}{C.GREEN}{'PROCESS COMPLETED — ⚡ MMK MODS ⚡'.center(62)}{C.RESET}{C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}║{C.RESET}{C.DIM}{'Check pp.txt & smngn.txt for matches'.center(62)}{C.RESET}{C.MAGENTA}║{C.RESET}")
    print(f"{C.MAGENTA}╚{'═'*62}╝{C.RESET}")
    print()




# ═══════════════════════════════════════════════════════════════
#  SECTION: HERMES PATCHER
# ═══════════════════════════════════════════════════════════════

import os
import sys
import subprocess
import zipfile
import re
import shutil
import urllib.request
import tempfile
import json
from pathlib import Path
from typing import List, Optional

class HermesPatcher:
    def __init__(self):
        self.current_dir = Path.cwd()
        self.required_packages = {
            'hbctool': {
                'wheel_file': 'hbctool-0.1.5-96-py3-none-any.whl',
                'install_cmd': ['pip', 'install', '--force-reinstall', 'hbctool-0.1.5-96-py3-none-any.whl'],
                'download_url': 'https://github.com/Kirlif/HBC-Tool/releases/download/96/hbctool-0.1.5-96-py3-none-any.whl'
            },
            'hermes_dec': {
                'wheel_file': 'hermes_dec-0.0.1-py3-none-any.whl',
                'install_cmd': ['pip', 'install', '--force-reinstall', 'hermes_dec-0.0.1-py3-none-any.whl'],
                'download_url': 'no'
            }
        }
        self.search_pattern = r'GetById.*(Reg8:\d+), Reg8:\d+, UInt8:\d+, UInt16:\d+\n.*\'(?i:ispremium|ispro\b|issubscribed|ispurchased|ispaid|haspurchase|isbought|hasaccess|isunlocked|isfullversion|isvip|islicensed|haslicense|isfree|istrial|getispremium|getispro|getpremium|getpro|getsubscribed|getsubscription|getpurchased|getpaid|getaccess|getunlocked|getfullversion|getvip|getlicensed|getfree|gettrial|haspremium|haspro|hassubscribed|haspurchased|haspaid|hasbought|hasunlocked|hasfullversion|hasvip|haslicensed|hasfree|hastrial|vip|isvip|hasvip|ispremium|premium|pro\b|vip|is_vip|is_premium|is_vip)\''
        self.replacement = r'LoadConstTrue     \1\nLoadConstTrue     \1\nLoadConstTrue     \1\n'
        self.keyword = 'Keywords'
        self.patched_count = 0
        self.patched_lines = []

    def setup_termux_path(self):
        termux_bin_path = "/data/data/com.termux/files/usr/bin"
        if os.path.exists(termux_bin_path) and termux_bin_path not in os.environ.get("PATH", ""):
            os.environ["PATH"] = f"{termux_bin_path}:{os.environ['PATH']}"
            ok(f"Termux PATH: {termux_bin_path}")

    def find_hbctool(self):
        self.setup_termux_path()
        hbctool_path = shutil.which("hbctool")
        if hbctool_path:
            return hbctool_path
        termux_path = "/data/data/com.termux/files/usr/bin/hbctool"
        if os.path.exists(termux_path):
            return termux_path
        current_path = self.current_dir / "hbctool"
        if os.path.exists(current_path):
            return str(current_path)
        return "hbctool"

    def is_package_installed(self, package_name: str) -> bool:
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'show', package_name],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def check_and_install_packages(self):
        banner("HERMES DEPENDENCIES", "hbctool / hermes_dec")
        pkgs = list(self.required_packages.items())
        for i, (pkg_name, pkg_info) in enumerate(pkgs, 1):
            progress_bar(i - 1, len(pkgs), f"check {pkg_name}")
            wheel_file = self.current_dir / pkg_info['wheel_file']
            if self.is_package_installed(pkg_name):
                ok(f"{pkg_name} already installed")
                progress_bar(i, len(pkgs), f"check {pkg_name}")
                continue
            info(f"Installing {pkg_name}...")
            if not wheel_file.exists():
                url = pkg_info['download_url']
                if url and url != 'no':
                    spinner(f"Download {pkg_info['wheel_file']}...", 1.0)
                    self.download_file(url, wheel_file.name)
                else:
                    warn(f"No download URL for {pkg_name} — skip if optional")
                    progress_bar(i, len(pkgs), f"check {pkg_name}")
                    continue
            try:
                spinner(f"pip install {pkg_name}...", 1.2)
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', '--force-reinstall', str(wheel_file)],
                    check=True, capture_output=True
                )
                ok(f"{pkg_name} installed")
            except subprocess.CalledProcessError as e:
                err(f"Failed to install {pkg_name}: {e}")
                sys.exit(1)
            progress_bar(i, len(pkgs), f"check {pkg_name}")

    def download_file(self, url: str, outname: str):
        info(f"Downloading: {url[:60]}...")
        req = urllib.request.Request(url, headers={'User-Agent': 'hermes_patcher/1.0'})
        with urllib.request.urlopen(req) as resp, open(outname, 'wb') as f:
            shutil.copyfileobj(resp, f)
        ok(f"Download finished: {outname}")

    def find_apkeditor_jar(self):
        if Path("APKEditor.jar").exists():
            return "APKEditor.jar"
        for f in os.listdir('.'):
            if f.lower().endswith('.jar') and "apkeditor" in f.lower():
                return f
        import glob
        jars = glob.glob("APKEditor*.jar") + glob.glob("*APKEditor*.jar")
        return jars[0] if jars else None

    def get_latest_apkeditor_url(self):
        api_url = "https://api.github.com/repos/REAndroid/APKEditor/releases/latest"
        try:
            with urllib.request.urlopen(api_url) as resp:
                data = json.load(resp)
            for asset in data.get("assets", []):
                if asset["name"].endswith(".jar") and "apkeditor" in asset["name"].lower():
                    return asset["name"], asset["browser_download_url"]
        except Exception as e:
            warn(f"GitHub API: {e}")
        return "APKEditor.jar", "https://github.com/REAndroid/APKEditor/releases/latest/download/APKEditor.jar"

    def ensure_apkeditor(self) -> str:
        banner("APKEDITOR", "merge / rebuild helper")
        jar = self.find_apkeditor_jar()
        if jar:
            ok(f"Found: {jar}")
            return jar
        spinner("Downloading APKEditor...", 1.5)
        name, url = self.get_latest_apkeditor_url()
        self.download_file(url, name)
        return name

    def has_java(self) -> bool:
        return shutil.which("java") is not None

    def check_java(self):
        banner("JAVA CHECK", "OpenJDK for APKEditor")
        if not self.has_java():
            err("Java not installed / not in PATH")
            info("Termux: pkg install openjdk-17")
            sys.exit(1)
        ok("Java available")

    def merge_apks(self, jarfile: str, apks_file: Path):
        if not self.has_java():
            err("Cannot merge APKS: Java not available")
            return None
        banner("MERGE SPLIT APK", apks_file.name)
        output_apk = self.current_dir / f"{apks_file.stem}_merged.apk"
        cmd = ["java", "-jar", jarfile, "m", "-i", str(apks_file), "-o", str(output_apk)]
        spinner(f"Merging → {output_apk.name}...", 1.5)
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            ok(f"Merged: {output_apk.name}")
            return output_apk
        except subprocess.CalledProcessError as e:
            err(f"Merge failed: {e}")
            if e.stderr:
                print(f"  {C.DIM}{e.stderr[:200]}{C.RESET}")
            return None

    def auto_clean_splitfolder(self, base_name: str):
        folder = Path(base_name).resolve()
        if folder.exists() and folder.is_dir():
            spinner(f"Hapus split folder {folder.name}...", 0.5)
            try:
                shutil.rmtree(folder)
                ok(f"Cleaned: {folder.name}")
            except Exception as e:
                warn(f"Could not remove {folder}: {e}")

    def find_apk_files(self):
        # Scan MMK app dirs + current_dir
        entries = mmk_list_apks((".apk", ".apks", ".xapk"))
        apk_files = [Path(fp) for fp, _, _ in entries]
        if not apk_files:
            for ext in ['.apk', '.apks', '.xapk']:
                apk_files.extend(list(self.current_dir.glob(f'*{ext}')))
        return apk_files

    def select_target_apk(self, apk_files):
        """Cool SELECT TARGET menu like Flutter"""
        files = []
        for p in apk_files:
            try:
                size = p.stat().st_size
            except OSError:
                size = 0
            files.append((str(p.resolve()), p.name, size))
        # reuse Flutter select_target if available
        if 'select_target' in globals():
            chosen = select_target(files, title="SELECT TARGET  •  HERMES APK")
            if chosen is None:
                return None
            return Path(chosen)
        # fallback simple
        for i, (path, name, size) in enumerate(files, 1):
            print(f"  {C.GREEN}{i:2d}{C.RESET}  {name}  {C.CYAN}{human_size(size)}{C.RESET}")
        print(f"  {C.RED} 0{C.RESET}  EXIT")
        try:
            c = input(f"\n{C.MAGENTA}𝙿𝚒𝚕𝚒𝚑 𝚗𝚘𝚖𝚘𝚛 ➤{C.RESET} ").strip()
            if c == "0":
                return None
            idx = int(c)
            if 1 <= idx <= len(files):
                return Path(files[idx - 1][0])
        except Exception:
            pass
        return files[0][0] and Path(files[0][0])

    def extract_assets_folder_from_apk(self, apk_path, dest_parent='.'):
        if not os.path.exists(apk_path):
            raise FileNotFoundError(f"APK not found: {apk_path}")
        banner("EXTRACT ASSETS", "assets/ + index.android.bundle")
        spinner("Scan ZIP entries...", 0.8)
        with zipfile.ZipFile(apk_path, 'r') as z:
            members = [m for m in z.namelist() if m.startswith('assets/')]
            if not members:
                raise RuntimeError("'assets/' folder not found in APK.")
            ok(f"{len(members)} entries di assets/")
            tmpdir = tempfile.mkdtemp(prefix='apk_extract_')
            try:
                files_only = [m for m in members if not m.endswith('/')]
                for i, m in enumerate(files_only, 1):
                    z.extract(m, path=tmpdir)
                    if i % 20 == 0 or i == len(files_only):
                        progress_bar(i, len(files_only), "extract")
                src_folder = os.path.join(tmpdir, 'assets')
                dst_folder = os.path.join(os.path.abspath(dest_parent), 'assets')
                if os.path.exists(dst_folder):
                    spinner("Hapus assets lama...", 0.4)
                    shutil.rmtree(dst_folder)
                shutil.move(src_folder, dst_folder)
                ok(f"assets/ → {dst_folder}")
                libso = os.path.join(dst_folder, 'index.android.bundle')
                if os.path.exists(libso):
                    dst_so = os.path.join(os.path.abspath(dest_parent), 'index.android.bundle')
                    if os.path.exists(dst_so):
                        os.remove(dst_so)
                    spinner("Copy index.android.bundle...", 0.4)
                    shutil.copy(libso, dst_so)
                    ok(f"bundle siap ({human_size(os.path.getsize(dst_so))})")
                else:
                    warn("index.android.bundle not found in assets")
            finally:
                shutil.rmtree(tmpdir, ignore_errors=True)

    def extract_bundle_file(self, extract_dir: Path) -> Path:
        bundle_path = extract_dir / "assets" / "index.android.bundle"
        if bundle_path.exists():
            target_bundle = self.current_dir / "index.android.bundle"
            shutil.copy2(bundle_path, target_bundle)
            ok("index.android.bundle extracted")
            return target_bundle
        warn("index.android.bundle not found in assets folder")
        existing_bundle = self.current_dir / "index.android.bundle"
        if existing_bundle.exists():
            ok("Using existing index.android.bundle")
            return existing_bundle
        err("No bundle file available")
        sys.exit(1)

    def disassemble_bundle(self, bundle_file: Path):
        banner("DISASSEMBLE", "hbctool disasm → instruction.hasm")
        disasm_dir = self.current_dir / "disasm"
        if disasm_dir.exists():
            spinner("Hapus disasm lama...", 0.5)
            try:
                shutil.rmtree(disasm_dir)
                ok("disasm/ cleaned")
            except Exception as e:
                warn(f"Could not remove disasm: {e}")
        hbctool_path = self.find_hbctool()
        info(f"hbctool: {hbctool_path}")
        spinner("Disassembling bundle (bisa lama)...", 1.5)
        try:
            cmd = f'"{hbctool_path}" disasm "{bundle_file}" "{disasm_dir}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=self.current_dir)
            if result.returncode == 0:
                ok("Bundle disassembled → disasm/")
            else:
                err(f"Disassembly failed (code {result.returncode})")
                if result.stderr:
                    print(f"  {C.DIM}{result.stderr[:300]}{C.RESET}")
                sys.exit(1)
        except Exception as e:
            err(f"Disassembly failed: {e}")
            sys.exit(1)

    def patch_instructions(self):
        banner("PATCH HASM", "premium / vip → LoadConstTrue")
        instruction_file = self.current_dir / "disasm" / "instruction.hasm"
        if not instruction_file.exists():
            err("instruction.hasm not found")
            sys.exit(1)
        info(f"Keyword target: {self.keyword}")
        spinner("Scanning instruction.hasm...", 1.0)
        with open(instruction_file, 'r', encoding='utf-8') as f:
            content = f.read()
        matches = list(re.finditer(self.search_pattern, content))
        self.patched_count = len(matches)
        if self.patched_count > 0:
            ok(f"Found {self.patched_count} match(es)")
            for i, match in enumerate(matches, 1):
                matched_text = match.group()
                lines = matched_text.split('\n')
                if lines:
                    short = lines[0].strip()[:70]
                    print(f"  {C.YELLOW}◆{C.RESET} {C.CYAN}#{i}{C.RESET}  {C.DIM}{short}{C.RESET}")
                    self.patched_lines.append(f"{i}. {lines[0].strip()}")
                    if len(lines) > 1:
                        premium_line = lines[1].strip()
                        if any(k in premium_line.lower() for k in ("premium", "vip", "pro", "subscri")):
                            self.patched_lines.append(f"   {premium_line}")
                            print(f"      {C.DIM}{premium_line[:70]}{C.RESET}")
            spinner("Writing LoadConstTrue x3...", 0.8)
            new_content = re.sub(self.search_pattern, self.replacement, content)
            with open(instruction_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            ok(f"Patched {self.patched_count} occurrence(s) → always True")
        else:
            err(f"No patterns found for: {self.keyword}")
            sys.exit(1)

    def show_patch_summary(self):
        if self.patched_count <= 0:
            return
        print()
        print(f"  {C.MAGENTA}╔{'═'*42}╗{C.RESET}")
        print(f"  {C.MAGENTA}║{C.RESET}  {C.BOLD}HERMES PATCH SUMMARY{C.RESET}{' '*20}{C.MAGENTA}║{C.RESET}")
        print(f"  {C.MAGENTA}║{C.RESET}  {C.CYAN}keyword : {self.keyword}{C.RESET}")
        print(f"  {C.MAGENTA}║{C.RESET}  {C.GREEN}patches : {self.patched_count}{C.RESET}")
        print(f"  {C.MAGENTA}║{C.RESET}  {C.DIM}effect  : always return True{C.RESET}")
        print(f"  {C.MAGENTA}╚{'═'*42}╝{C.RESET}")
        print()

    def assemble_bundle(self):
        banner("ASSEMBLE", "hbctool asm → index.android.bundle")
        disasm_dir = self.current_dir / "disasm"
        output_bundle = self.current_dir / "index.android.bundle"
        hbctool_path = self.find_hbctool()
        spinner("Assembling bytecode...", 1.5)
        try:
            cmd = f'"{hbctool_path}" asm "{disasm_dir}" "{output_bundle}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=self.current_dir)
            if result.returncode == 0:
                size = human_size(output_bundle.stat().st_size) if output_bundle.exists() else "?"
                ok(f"Bundle assembled ({size})")
            else:
                err(f"Assembly failed (code {result.returncode})")
                if result.stderr:
                    print(f"  {C.DIM}{result.stderr[:300]}{C.RESET}")
                sys.exit(1)
        except Exception as e:
            err(f"Assembly failed: {e}")
            sys.exit(1)

    def replace_bundle_in_apk(self, apk_path, patched_lib):
        banner("REPACK APK", "inject patched index.android.bundle")
        spinner("Writing ZIP entries...", 1.0)
        tmp_apk = apk_path + ".tmp"
        replaced = False
        with zipfile.ZipFile(apk_path, 'r') as zin, zipfile.ZipFile(tmp_apk, 'w') as zout:
            items = zin.infolist()
            for i, item in enumerate(items, 1):
                if item.filename == "assets/index.android.bundle":
                    zout.write(patched_lib, item.filename)
                    replaced = True
                    print(f"  {C.GREEN}│  ★ replaced {item.filename}{C.RESET}")
                else:
                    zout.writestr(item, zin.read(item.filename))
                if i % 40 == 0 or i == len(items):
                    progress_bar(i, len(items), "repack")
        os.replace(tmp_apk, apk_path)
        if replaced:
            ok(f"Bundle injected → {os.path.basename(apk_path)}")
        else:
            warn("assets/index.android.bundle not found in APK")

    def repack_apk(self, original_apk: Path):
        patched_bundle = self.current_dir / "index.android.bundle"
        if not patched_bundle.exists():
            err("Patched bundle not found")
            sys.exit(1)
        try:
            # tulis ke out/patched — jangan timpa app/
            dest = mmk_output("patched", f"{original_apk.stem}_hermes_patched.apk")
            output_apk = Path(dest)
            spinner(f"Copy → {output_apk.name}...", 0.6)
            shutil.copy2(original_apk, output_apk)
            self.replace_bundle_in_apk(str(output_apk), str(patched_bundle))
            ok(f"Output: {output_apk.name}")
            info(f"Direktori: {output_apk.parent}")
            return output_apk
        except Exception as e:
            err(f"Repack failed: {e}")
            sys.exit(1)

    def extract_apk(self, apk_file: Path) -> Path:
        banner("EXTRACT APK", apk_file.name)
        extract_dir = self.current_dir / apk_file.stem
        extract_dir.mkdir(exist_ok=True)
        try:
            self.extract_assets_folder_from_apk(apk_file, extract_dir)
            ok(f"Extract dir: {extract_dir.name}")
            return extract_dir
        except Exception as e:
            err(f"Extract failed: {e}")
            sys.exit(1)

    def clean_temp_files(self, extract_dir: Path, working_apk: Path, original_apk: Path):
        banner("CLEANUP", "hapus file sementara")
        disasm_dir = self.current_dir / "disasm"
        if disasm_dir.exists():
            spinner("Hapus disasm/...", 0.4)
            shutil.rmtree(disasm_dir)
            ok("disasm/ removed")
        bundle_file = self.current_dir / "index.android.bundle"
        if bundle_file.exists():
            spinner("Hapus index.android.bundle...", 0.3)
            bundle_file.unlink()
            ok("index.android.bundle removed")
        if extract_dir.exists():
            spinner(f"Hapus {extract_dir.name}/...", 0.4)
            shutil.rmtree(extract_dir)
            ok("extract dir removed")
        if working_apk != original_apk and working_apk.exists():
            spinner("Hapus merged APK sementara...", 0.3)
            working_apk.unlink()
            ok("temp merged APK removed")

    def run(self):
        banner("HERMES PATCHER", "index.android.bundle  •  premium → True")
        info(f"Target keyword: {self.keyword}")
        print()

        self.setup_termux_path()
        self.check_java()
        self.check_and_install_packages()
        apkeditor_jar = self.ensure_apkeditor()

        apk_files = self.find_apk_files()
        if not apk_files:
            err(f"No APK / APKS / XAPK in {MMK_APP_DIR}")
            sys.exit(1)

        selected_file = self.select_target_apk(apk_files)
        if selected_file is None:
            info("Dibatalkan")
            return
        if not isinstance(selected_file, Path):
            selected_file = Path(selected_file)

        ok(f"Target: {selected_file.name}")
        working_apk = selected_file
        if selected_file.suffix.lower() in ['.apks', '.xapk']:
            merged_apk = self.merge_apks(apkeditor_jar, selected_file)
            if merged_apk:
                working_apk = merged_apk
                self.auto_clean_splitfolder(selected_file.stem)
            else:
                err("Could not merge APKS")
                sys.exit(1)

        extract_dir = self.extract_apk(working_apk)
        bundle_file = self.extract_bundle_file(extract_dir)
        self.disassemble_bundle(bundle_file)
        self.patch_instructions()
        self.show_patch_summary()
        self.assemble_bundle()
        patched_apk = self.repack_apk(working_apk)
        self.clean_temp_files(extract_dir, working_apk, selected_file)

        print()
        print(f"{C.MAGENTA}╔{'═'*50}╗{C.RESET}")
        print(f"{C.MAGENTA}║{C.RESET}{C.BOLD}{C.GREEN}{'HERMES PATCH COMPLETE'.center(50)}{C.RESET}{C.MAGENTA}║{C.RESET}")
        print(f"{C.MAGENTA}║{C.RESET}{C.DIM}{('Output: ' + patched_apk.name).center(50)}{C.RESET}{C.MAGENTA}║{C.RESET}")
        print(f"{C.MAGENTA}║{C.RESET}{C.DIM}{('Patches: ' + str(self.patched_count)).center(50)}{C.RESET}{C.MAGENTA}║{C.RESET}")
        print(f"{C.MAGENTA}╚{'═'*50}╝{C.RESET}")
        print()


def hermes_main():
    """Main entry point for Hermes Patcher"""
    try:
        patcher = HermesPatcher()
        patcher.run()
    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}⚠ Process interrupted by user{C.RESET}")
        sys.exit(1)
    except Exception as e:
        err(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



# ═══════════════════════════════════════════════════════════════
#  SECTION: MTCR APPLY TOOL
# ═══════════════════════════════════════════════════════════════


"""
MTCR Apply Tool v2.0
A professional tool for applying MTCR patches to APK files in Termux
Author: MMK MOD
Core: mtcr-apply.jar by @NullRE
"""

import os
import sys
import subprocess
import shutil
import secrets
import string
import json
import signal
import re
import time
import threading
import argparse
import hashlib
from pathlib import Path
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# ----------------- Metadata -----------------
__version__ = "2.0.0"
__author__ = "MMK MOD"
__license__ = "MIT"
__repository__ = "https://github.com/issmali/mtcr-apply-tool"

# ----------------- Konfigurasi -----------------
CONFIG_FILE = "mtcr_config.json"
HISTORY_FILE = "mtcr_history.json"
DEFAULT_CONFIG = {
    "jar_name": "mtcr-apply.jar",
    "log_file": "mtcr_apply.log",
    "history_file": "mtcr_history.json",
    "backup_enabled": True,
    "max_retries": 3,
    "timeout": 300,
    "output_dir": "output",
    "temp_dir": "temp",
    "max_workers": 3,
    "min_free_space_mb": 500,
    "use_colors": True,
    "verbose_mode": False,
    "save_history": True,
    "max_history_items": 10,
    "auto_clean_temp": True,
    "dry_run": False
}

# ----------------- Global State -----------------
CONFIG = {}
USE_COLORS = True
VERBOSE = False
DRY_RUN = False

# ----------------- Colors -----------------
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'

def supports_color():
    """Check if terminal supports colors"""
    if os.environ.get('NO_COLOR'):
        return False
    if os.environ.get('TERM') == 'dumb':
        return False
    return sys.platform != 'win32' or 'ANSICON' in os.environ or 'WT_SESSION' in os.environ

def colorize(text, color):
    if USE_COLORS:
        return f"{color}{text}{Colors.END}"
    return text

# ----------------- Logging Setup -----------------
def setup_logging():
    """Setup logging dengan rotation sederhana"""
    log_file = CONFIG.get("log_file", "mtcr_apply.log")
    
    # Check log size, rotate if > 5MB
    if Path(log_file).exists() and Path(log_file).stat().st_size > 5 * 1024 * 1024:
        backup = f"{log_file}.old"
        if Path(backup).exists():
            Path(backup).unlink()
        Path(log_file).rename(backup)
    
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG if VERBOSE else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

# ----------------- Config Management -----------------
def load_config():
    """Load config dengan auto-generate jika tidak ada"""
    global CONFIG_FILE
    
    if not Path(CONFIG_FILE).exists():
        create_default_config()
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            config = {**DEFAULT_CONFIG, **user_config}
            
            # Validate critical paths
            if not config.get("jar_name"):
                config["jar_name"] = DEFAULT_CONFIG["jar_name"]
                
            return config
    except Exception as e:
        print(f"[!] Error loading config: {e}")
        print("[*] Using default configuration")
        return DEFAULT_CONFIG.copy()

def create_default_config():
    """Create default config file"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        print(f"[+] Created default config: {CONFIG_FILE}")
    except Exception as e:
        print(f"[!] Could not create config: {e}")

def save_config():
    """Save current config to file"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(CONFIG, f, indent=2)
        return True
    except Exception as e:
        print_error(f"Failed to save config: {e}")
        return False

# ----------------- History Management -----------------
def load_history():
    """Load recent files history"""
    history_file = CONFIG.get("history_file", "mtcr_history.json")
    if Path(history_file).exists():
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"apks": [], "mtcrs": [], "outputs": []}

def save_history(history):
    """Save history dengan limit"""
    if not CONFIG.get("save_history", True):
        return
        
    history_file = CONFIG.get("history_file", "mtcr_history.json")
    max_items = CONFIG.get("max_history_items", 10)
    
    # Trim to max items
    for key in history:
        history[key] = history[key][:max_items]
    
    try:
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logging.warning(f"Could not save history: {e}")

def add_to_history(category, filepath):
    """Add file to history"""
    if not CONFIG.get("save_history", True) or not filepath:
        return
        
    history = load_history()
    if filepath not in history[category]:
        history[category].insert(0, filepath)
        save_history(history)

# ----------------- Utility Functions (MMK MODS unified UI) -----------------
def print_success(msg):
    try:
        ok(msg)
    except Exception:
        print(colorize("[+] " + msg, Colors.GREEN))

def print_error(msg):
    try:
        err(msg)
    except Exception:
        print(colorize("[!] " + msg, Colors.RED))

def print_info(msg):
    try:
        info(msg)
    except Exception:
        print(colorize("[*] " + msg, Colors.BLUE))

def print_warning(msg):
    try:
        warn(msg)
    except Exception:
        print(colorize("[~] " + msg, Colors.YELLOW))

def print_verbose(msg):
    if VERBOSE:
        print(f"  {C.DIM}[V] {msg}{C.RESET}" if 'C' in dir() else colorize("[V] " + msg, Colors.DIM))

def print_banner_text(text):
    print(f"{C.CYAN}{C.BOLD}{text}{C.RESET}" if 'C' in dir() else colorize(text, Colors.CYAN + Colors.BOLD))

def clear_screen():
    os.system("clear" if os.name != 'nt' else "cls")

def mtcr_banner():
    logo = [
        r"  ███╗   ███╗████████╗ ██████╗██████╗ ",
        r"  ████╗ ████║╚══██╔══╝██╔════╝██╔══██╗",
        r"  ██╔████╔██║   ██║   ██║     ██████╔╝",
        r"  ██║╚██╔╝██║   ██║   ██║     ██╔══██╗",
        r"  ██║ ╚═╝ ██║   ██║   ╚██████╗██║  ██║",
        r"  ╚═╝     ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝",
    ]
    print()
    for line in logo:
        print(f"{C.CYAN}{line}{C.RESET}")
    print(f"{C.MAGENTA}{'═'*50}{C.RESET}")
    print(f"{C.BOLD}{C.WHITE}{'MTCR APPLY TOOL  •  v' + str(__version__).center(0)}{C.RESET}".ljust(0))
    print(f"  {C.BOLD}{C.WHITE}MTCR Apply Tool v{__version__}{C.RESET}")
    print(f"  {C.DIM}Termux Android Patching Tool  ·  MMK MODS{C.RESET}")
    print(f"{C.MAGENTA}{'═'*50}{C.RESET}")
    print()

def exit_message(code=0):
    print_info("Thanks for using MTCR Apply Tool!")
    print_info("Stay safe and happy patching!")
    if CONFIG.get("auto_clean_temp", True):
        cleanup_temp()
    sys.exit(code)

# ----------------- Signal Handler -----------------
def signal_handler(signum, frame):
    print_error("\n\nInterrupted! Cleaning up...")
    cleanup_temp()
    sys.exit(1)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def cleanup_temp():
    """Bersihkan file temporary"""
    temp_dirs = [
        CONFIG.get("temp_dir", "temp"),
        ".cache",
        "temp",
        "__pycache__"
    ]
    for d in temp_dirs:
        if Path(d).exists():
            try:
                shutil.rmtree(d, ignore_errors=True)
                logging.debug(f"Cleaned up: {d}")
            except:
                pass

# ----------------- Decorator for Safe Execution -----------------
def safe_execute(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            print_error("\nOperation cancelled by user")
            return None
        except Exception as e:
            print_error(f"Unexpected error in {func.__name__}: {str(e)}")
            if VERBOSE:
                import traceback
                traceback.print_exc()
            logging.error(f"Exception in {func.__name__}: {e}", exc_info=True)
            return None
    return wrapper

# ----------------- Disk Space Check -----------------
def check_disk_space(path=".", required_mb=None, silent=False):
    """Check apakah disk space cukup"""
    if required_mb is None:
        required_mb = CONFIG.get("min_free_space_mb", 500)
    
    try:
        stat = shutil.disk_usage(path)
        free_mb = stat.free // (1024 * 1024)
        
        if free_mb < required_mb:
            if not silent:
                print_error(f"Insufficient disk space: {free_mb}MB free, {required_mb}MB required")
            return False
            
        if not silent:
            print_verbose(f"Disk space OK: {free_mb}MB free")
        return True
    except Exception as e:
        if not silent:
            print_error(f"Could not check disk space: {e}")
        return False

# ----------------- Dependency Checks -----------------
@safe_execute
def check_python():
    """Check Python installation"""
    python_path = shutil.which("python") or shutil.which("python3")
    
    if python_path:
        try:
            version_output = subprocess.check_output(
                [python_path, "--version"], 
                stderr=subprocess.STDOUT, 
                text=True,
                timeout=5
            )
            version_str = version_output.strip()
            print_success(f"Python detected: {version_str}")
            logging.info(f"Python detected: {version_str}")
            return True
        except Exception as e:
            print_error(f"Error checking Python: {e}")

    print_info("Python not found. Attempting auto-install...")
    if shutil.which("pkg"):
        try:
            print_info("Updating packages...")
            subprocess.run(["pkg", "update", "-y"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print_info("Installing Python...")
            subprocess.run(["pkg", "install", "-y", "python"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print_success("Python installed successfully")
            return shutil.which("python") is not None or shutil.which("python3") is not None
        except Exception as e:
            print_error(f"Failed to install Python: {e}")
            return False
    return False

@safe_execute
def check_java():
    """Check Java installation dengan version check detail"""
    java_path = shutil.which("java")
    
    if java_path:
        try:
            result = subprocess.run(
                ["java", "-version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            output = result.stderr + result.stdout
            
            # Parse versi
            version_match = re.search(r'version "(\d+)(?:\.(\d+))?(?:\.(\d+))?', output)
            if version_match:
                major = int(version_match.group(1))
                if major >= 17:
                    print_success(f"Java {major} detected ✓")
                    return True
                else:
                    print_warning(f"Java {major} detected (requires 17+)")
            else:
                # Check for openjdk version format
                openjdk_match = re.search(r'OpenJDK.*?(\d+)', output)
                if openjdk_match:
                    major = int(openjdk_match.group(1))
                    if major >= 17:
                        print_success(f"OpenJDK {major} detected ✓")
                        return True
                        
        except Exception as e:
            print_error(f"Error checking Java: {e}")

    print_info("Java not found or outdated. Attempting auto-install...")
    if shutil.which("pkg"):
        try:
            print_info("Installing OpenJDK 17...")
            subprocess.run(["pkg", "update", "-y"], check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["pkg", "install", "-y", "openjdk-17"], check=True, stdout=subprocess.DEVNULL)
            print_success("Java installed successfully")
            return shutil.which("java") is not None
        except Exception as e:
            print_error(f"Failed to install Java: {e}")
            return False
    return False

def check_jar():
    """Check if JAR file exists"""
    jar_name = CONFIG.get("jar_name", "mtcr-apply.jar")
    if not Path(jar_name).exists():
        print_error(f"{jar_name} not found in current directory!")
        print_info("Please ensure mtcr-apply.jar is in the same folder as this script")
        return False
    return True

# ----------------- File Validation -----------------
def calculate_hash(filepath, algorithm="md5"):
    """Calculate file hash untuk integrity check"""
    try:
        hasher = hashlib.new(algorithm)
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logging.error(f"Hash calculation failed: {e}")
        return None

def validate_apk(file_path):
    """Validasi APK komprehensif"""
    try:
        # Check exists
        if not Path(file_path).exists():
            return False, "File does not exist"
            
        # Check size
        file_size = os.path.getsize(file_path)
        if file_size < 1024:
            return False, f"File too small ({file_size} bytes)"
        if file_size > 500 * 1024 * 1024:  # Max 500MB
            return False, f"File suspiciously large ({file_size / 1024 / 1024:.1f} MB)"
        
        # Check ZIP header
        with open(file_path, 'rb') as f:
            header = f.read(4)
            valid_headers = [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08']
            if header not in valid_headers:
                return False, "Invalid APK: Not a valid ZIP archive"
            
            # Check for AndroidManifest.xml (basic APK validation)
            # This is a simple check, not comprehensive
            f.seek(0)
            content = f.read(8192)  # Read first 8KB
            if b'AndroidManifest.xml' not in content and b'classes.dex' not in content:
                # Not necessarily invalid, just suspicious
                print_warning("APK structure unusual (no manifest in header)")
                
        return True, f"Valid ({file_size / 1024 / 1024:.1f} MB)"
    except Exception as e:
        return False, f"Validation error: {e}"

def validate_mtcr(file_path):
    """Validasi MTCR file"""
    try:
        if not Path(file_path).exists():
            return False, "File does not exist"
            
        size = os.path.getsize(file_path)
        if size == 0:
            return False, "File is empty"
        if size > 50 * 1024 * 1024:  # Max 50MB
            return False, "File suspiciously large"
            
        return True, f"Valid ({size / 1024:.1f} KB)"
    except Exception as e:
        return False, str(e)

# ----------------- Backup & Restore -----------------
def create_backup(file_path):
    """Buat backup dengan metadata"""
    if not CONFIG.get("backup_enabled", True):
        return None
        
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_name = Path(file_path).stem
    backup_name = f"{original_name}_{timestamp}.apk.bak"
    backup_path = backup_dir / backup_name
    
    try:
        shutil.copy2(file_path, backup_path)
        
        # Save metadata
        meta = {
            "original": str(file_path),
            "backup_time": timestamp,
            "size": os.path.getsize(file_path),
            "hash": calculate_hash(file_path)
        }
        meta_path = backup_path.with_suffix('.json')
        with open(meta_path, 'w') as f:
            json.dump(meta, f, indent=2)
            
        print_verbose(f"Backup created: {backup_path}")
        logging.info(f"Backup created: {backup_path}")
        return str(backup_path)
    except Exception as e:
        print_warning(f"Backup failed: {e}")
        return None

def restore_backup(backup_path, original_path):
    """Restore dari backup"""
    if not backup_path or not Path(backup_path).exists():
        return False
        
    try:
        # Verify backup integrity if metadata exists
        meta_path = Path(backup_path).with_suffix('.json')
        if meta_path.exists():
            with open(meta_path, 'r') as f:
                meta = json.load(f)
            current_hash = calculate_hash(backup_path)
            if current_hash != meta.get("hash"):
                print_warning("Backup integrity check failed!")
                return False
        
        shutil.copy2(backup_path, original_path)
        print_info(f"Restored from backup: {backup_path}")
        logging.info(f"Restored: {backup_path} -> {original_path}")
        return True
    except Exception as e:
        print_error(f"Restore failed: {e}")
        return False

def list_backups():
    """List available backups"""
    backup_dir = Path("backups")
    if not backup_dir.exists():
        return []
    
    backups = sorted(backup_dir.glob("*.apk.bak"), key=lambda x: x.stat().st_mtime, reverse=True)
    return [str(b) for b in backups]

# ----------------- File Utilities -----------------
def list_files(ext, directory="."):
    """List files — untuk .apk scan juga folder app/"""
    try:
        if str(ext).lower() in (".apk", ".apks", ".xapk", ".aab"):
            entries = mmk_list_apks((ext,) if isinstance(ext, str) else tuple(ext))
            if entries:
                return [e[1].split("/")[-1] if "/" in str(e[1]) else e[1] for e in entries]
        files = sorted([f.name for f in Path(directory).glob(f"*{ext}") if f.is_file()])
        app = Path(MMK_APP_DIR)
        if app.is_dir() and str(app.resolve()) != str(Path(directory).resolve()):
            files += sorted([f.name for f in app.glob(f"*{ext}") if f.is_file()])
        return sorted(set(files))
    except Exception:
        return []


def scan_directory():
    """Scan directory untuk auto-detect files"""
    apks = list_files(".apk")
    mtcrs = list_files(".mtcr")
    return apks, mtcrs

def pick_file(files, title, history_key=None):
    """Enhanced file picker dengan history"""
    if not files:
        print_error(f"No {title} files found in current directory")
        # Try to suggest from history
        history = load_history()
        if history_key and history.get(history_key):
            print_info("Recent files:")
            for i, f in enumerate(history[history_key][:3], 1):
                if Path(f).exists():
                    print(f"  {i}. {f}")
        return None
        
    # Show recent first if available
    history = load_history()
    recent = []
    if history_key:
        recent = [f for f in history.get(history_key, []) if f in files]
        other = [f for f in files if f not in recent]
        files = recent + other
    
    while True:
        print_info(f"Select {title}:")
        
        # Mark recent files
        for i, f in enumerate(files, 1):
            marker = " ★" if f in recent else ""
            print(f" {i}) {f}{marker}")
            
        print(" 0) Enter path manually")
        print(" S) Search file")
        
        choice = input("[?] Enter number: ").strip().lower()
        
        if choice == '0':
            custom = input("[?] Enter full path: ").strip()
            if Path(custom).exists():
                return custom
            print_error("File not found")
            continue
            
        if choice == 's':
            search = input("[?] Search term: ").strip().lower()
            matches = [f for f in files if search in f.lower()]
            if matches:
                print_info(f"Found {len(matches)} matches:")
                for i, m in enumerate(matches, 1):
                    print(f"  {i}. {m}")
                sub = input("[?] Select: ").strip()
                if sub.isdigit() and 1 <= int(sub) <= len(matches):
                    return matches[int(sub) - 1]
            else:
                print_error("No matches found")
            continue
        
        if choice.isdigit() and 1 <= int(choice) <= len(files):
            file_selected = files[int(choice) - 1]
            
            # Validate
            if file_selected.endswith('.apk'):
                valid, msg = validate_apk(file_selected)
            elif file_selected.endswith('.mtcr'):
                valid, msg = validate_mtcr(file_selected)
            else:
                valid = os.path.getsize(file_selected) > 0
                msg = "Empty file" if not valid else "Valid"
            
            if not valid:
                print_error(f"Invalid: {msg}")
            else:
                print_verbose(f"Selected: {file_selected} ({msg})")
                return file_selected
        else:
            print_error("Invalid selection")

def pick_multiple_files(files, title):
    """Select multiple files dengan order preservation"""
    if not files:
        print_error(f"No {title} files found")
        return []
    
    print_info(f"Select {title} (comma-separated or range, e.g., 1,3,5 or 1-5):")
    for i, f in enumerate(files, 1):
        print(f" {i}) {f}")
    
    while True:
        choice = input("[?] Enter selection: ").strip()
        if not choice:
            return []
        
        selected_indices = []
        parts = choice.split(',')
        valid = True
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    if not (1 <= start <= len(files) and 1 <= end <= len(files)):
                        print_error(f"Range out of bounds: {part}")
                        valid = False
                        break
                    selected_indices.extend(range(start, end + 1))
                except:
                    print_error(f"Invalid range: {part}")
                    valid = False
                    break
            else:
                try:
                    num = int(part)
                    if not 1 <= num <= len(files):
                        print_error(f"Number out of range: {num}")
                        valid = False
                        break
                    selected_indices.append(num)
                except:
                    print_error(f"Invalid number: {part}")
                    valid = False
                    break
        
        # Remove duplicates while preserving order
        seen = set()
        unique_indices = [x for x in selected_indices if not (x in seen or seen.add(x))]
        
        if valid and unique_indices:
            selected_files = [files[i-1] for i in unique_indices]
            
            # Validate all
            invalid = []
            for f in selected_files:
                if f.endswith('.apk'):
                    ok, msg = validate_apk(f)
                elif f.endswith('.mtcr'):
                    ok, msg = validate_mtcr(f)
                else:
                    ok = os.path.getsize(f) > 0
                    msg = "Empty"
                if not ok:
                    invalid.append(f"{f}: {msg}")
            
            if invalid:
                print_error("Some files invalid:")
                for inv in invalid:
                    print(f"  - {inv}")
                continue
            
            print_info("Selected:")
            for f in selected_files:
                print(f"  → {f}")
                
            confirm = input("[?] Confirm? [Y/n]: ").lower()
            if confirm != 'n':
                return selected_files
        else:
            print_error("No valid selection")

def auto_output_name(prefix=""):
    """Generate unique output name"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    chars = string.ascii_lowercase + string.digits
    rand = "".join(secrets.choice(chars) for _ in range(4))
    
    output_dir = CONFIG.get("output_dir", "output")
    Path(output_dir).mkdir(exist_ok=True)
    
    output = os.path.join(output_dir, f"{prefix}patched-{timestamp}-{rand}.apk")
    
    # Ensure unique
    counter = 1
    while Path(output).exists():
        rand = "".join(secrets.choice(chars) for _ in range(4))
        output = os.path.join(output_dir, f"{prefix}patched-{timestamp}-{rand}.apk")
        counter += 1
        if counter > 100:  # Safety break
            break
            
    return output

def confirm_overwrite(filename):
    """Confirm overwrite dengan detail"""
    if Path(filename).exists():
        size = os.path.getsize(filename) / 1024 / 1024
        print_warning(f"File exists: {filename} ({size:.1f} MB)")
        choice = input("[?] Overwrite? [y/N]: ").lower()
        return choice == 'y'
    return True

# ----------------- Progress Indicators -----------------
class ProgressBar:
    def __init__(self, total, desc="Processing"):
        self.total = total
        self.current = 0
        self.desc = desc
        self.start_time = time.time()
        self._lock = threading.Lock()
        
    def update(self, increment=1):
        with self._lock:
            self.current += increment
            percent = (self.current / self.total) * 100
            elapsed = time.time() - self.start_time
            eta = (elapsed / self.current) * (self.total - self.current) if self.current > 0 else 0
            
            bar_length = 30
            filled = int(bar_length * self.current // self.total)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            status = f"\r{self.desc}: [{bar}] {percent:.1f}% | {self.current}/{self.total}"
            if eta > 0:
                status += f" | ETA: {eta:.0f}s"
            
            print(status, end='', flush=True)
        
    def finish(self):
        with self._lock:
            print()

class Spinner:
    def __init__(self, message="Processing"):
        self.spinner_cycle = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.running = False
        self.message = message
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.daemon = True
        self.thread.start()

    def _spin(self):
        i = 0
        while self.running:
            print(f"\r{self.message} {self.spinner_cycle[i % len(self.spinner_cycle)]}", end="", flush=True)
            i += 1
            time.sleep(0.08)
        print("\r" + " " * (len(self.message) + 5) + "\r", end="", flush=True)

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)

# ----------------- Core Patch Logic -----------------
def run_patch_command(apk, mtcr, output, reverse=False):
    """Execute patch command dengan comprehensive error handling"""
    jar_name = CONFIG.get("jar_name", "mtcr-apply.jar")
    cmd = ["java", "-jar", jar_name]
    
    if reverse:
        cmd.append("-r")
    cmd.extend(["-i", apk, "-p", mtcr, "-o", output])
    
    if DRY_RUN:
        print_info(f"[DRY RUN] Would execute: {' '.join(cmd)}")
        return True, "Dry run success"
    
    max_retries = CONFIG.get("max_retries", 3)
    timeout = CONFIG.get("timeout", 300)
    
    for attempt in range(max_retries):
        try:
            print_verbose(f"Attempt {attempt + 1}/{max_retries}: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate(timeout=timeout)
            
            if process.returncode == 0:
                # Verify output file exists and is valid
                if Path(output).exists() and os.path.getsize(output) > 0:
                    return True, "Success"
                else:
                    return False, "Output file not created or empty"
            else:
                error_msg = stderr.strip() if stderr else "Unknown error"
                if "out of memory" in error_msg.lower():
                    return False, "Java OutOfMemoryError - try increasing Termux memory"
                if "permission" in error_msg.lower():
                    return False, "Permission denied - check file permissions"
                    
                if attempt < max_retries - 1:
                    print_warning(f"Attempt {attempt + 1} failed, retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return False, f"Failed: {error_msg[:200]}"
                    
        except subprocess.TimeoutExpired:
            process.kill()
            if attempt < max_retries - 1:
                print_warning(f"Timeout on attempt {attempt + 1}, retrying...")
            else:
                return False, f"Timeout after {timeout}s"
        except Exception as e:
            return False, f"Exception: {str(e)}"
    
    return False, "Max retries exceeded"

# ----------------- Application Modes -----------------
@safe_execute
def apply_single(reverse=False):
    """Single patch mode"""
    if not check_disk_space():
        return
        
    if not check_jar():
        return

    apks = list_files(".apk")
    apk = pick_file(apks, "APK file", "apks")
    if not apk:
        return

    mtcrs = list_files(".mtcr")
    mtcr = pick_file(mtcrs, "MTCR patch", "mtcrs")
    if not mtcr:
        return

    default_output = auto_output_name()
    output = input(f"[?] Output name [Enter for {default_output}]: ").strip() or default_output
    
    if not confirm_overwrite(output):
        print_info("Canceled.")
        return
    
    print_info(f"Output: {output}")

    # Backup
    backup_path = create_backup(apk)
    
    # Execute
    spinner = Spinner("Applying patch...")
    spinner.start()
    
    success, message = run_patch_command(apk, mtcr, output, reverse)
    
    spinner.stop()
    
    if success:
        print_success("Patch applied successfully!")
        print_info(f"Output: {output}")
        
        # Add to history
        add_to_history("apks", apk)
        add_to_history("mtcrs", mtcr)
        add_to_history("outputs", output)
        
        # Cleanup backup
        if backup_path and Path(backup_path).exists():
            Path(backup_path).unlink()
            if Path(backup_path).with_suffix('.json').exists():
                Path(backup_path).with_suffix('.json').unlink()
                
        logging.info(f"SINGLE SUCCESS: {apk} + {mtcr} -> {output}")
        
        # Show file info
        if Path(output).exists():
            size = os.path.getsize(output) / 1024 / 1024
            print_info(f"File size: {size:.1f} MB")
    else:
        print_error(f"Failed: {message}")
        logging.error(f"SINGLE FAILED: {apk} + {mtcr} | {message}")
        
        if backup_path:
            print_info("Attempting to restore backup...")
            if restore_backup(backup_path, apk):
                print_success("Backup restored")
            else:
                print_error("Backup restore failed")

def apply_patch_worker(args):
    """Worker untuk parallel processing"""
    idx, total, apk, mtcr, output_base, reverse = args
    
    apk_name = Path(apk).stem
    mtcr_name = Path(mtcr).stem
    
    # Create output path
    out_dir = Path(output_base) / apk_name
    out_dir.mkdir(parents=True, exist_ok=True)
    
    output = out_dir / f"{apk_name}_{mtcr_name}_patched.apk"
    counter = 1
    while output.exists():
        output = out_dir / f"{apk_name}_{mtcr_name}_patched_{counter}.apk"
        counter += 1
    
    # Backup
    backup_path = create_backup(apk) if CONFIG.get("backup_enabled") else None
    
    # Execute
    success, message = run_patch_command(apk, mtcr, str(output), reverse)
    
    if success:
        if backup_path and Path(backup_path).exists():
            Path(backup_path).unlink()
            if Path(backup_path).with_suffix('.json').exists():
                Path(backup_path).with_suffix('.json').unlink()
        return (idx, apk, mtcr, str(output), True, "Success")
    else:
        if backup_path:
            restore_backup(backup_path, apk)
        return (idx, apk, mtcr, str(output), False, message)

@safe_execute
def apply_paired(reverse=False, parallel=False):
    """Paired mode: one-to-one matching"""
    if not check_disk_space(required_mb=CONFIG.get("min_free_space_mb", 500) * 2):
        return
        
    if not check_jar():
        return

    # Select files
    apks = list_files(".apk")
    print_info("Select APKs (order matters):")
    selected_apks = pick_multiple_files(apks, "APK")
    if not selected_apks:
        return

    mtcrs = list_files(".mtcr")
    print_info("Select MTCRs (order matters):")
    selected_mtcrs = pick_multiple_files(mtcrs, "MTCR")
    if not selected_mtcrs:
        return

    if len(selected_apks) != len(selected_mtcrs):
        print_error(f"Count mismatch: {len(selected_apks)} APKs vs {len(selected_mtcrs)} MTCRs")
        return

    # Output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_base = Path(CONFIG.get("output_dir", "output")) / f"batch_{timestamp}"
    output_base.mkdir(parents=True, exist_ok=True)

    # Preview
    print("\n" + "─" * 50)
    print_info("PATCH QUEUE:")
    for i, (a, m) in enumerate(zip(selected_apks, selected_mtcrs), 1):
        print(f"  {i}. {a}")
        print(f"     └─> {m}")
    print("─" * 50)

    if input("[?] Proceed? [y/N]: ").lower() != 'y':
        print_info("Canceled.")
        return

    total = len(selected_apks)
    success_count = 0
    failed_items = []

    if parallel and total > 1:
        # Parallel mode
        print_info(f"Running parallel with {CONFIG.get('max_workers', 3)} workers...")
        
        tasks = [(i, total, a, m, output_base, reverse) 
                for i, (a, m) in enumerate(zip(selected_apks, selected_mtcrs), 1)]
        
        progress = ProgressBar(total, "Patching")
        completed = 0
        
        with ThreadPoolExecutor(max_workers=CONFIG.get('max_workers', 3)) as executor:
            futures = {executor.submit(apply_patch_worker, t): t for t in tasks}
            
            for future in as_completed(futures):
                result = future.result()
                idx, apk, mtcr, out, ok, msg = result
                
                completed += 1
                progress.update()
                
                if ok:
                    success_count += 1
                    add_to_history("apks", apk)
                    add_to_history("mtcrs", mtcr)
                    add_to_history("outputs", out)
                else:
                    failed_items.append((idx, apk, mtcr, msg))
        
        progress.finish()
    else:
        # Sequential mode
        progress = ProgressBar(total, "Patching")
        
        for idx, (apk, mtcr) in enumerate(zip(selected_apks, selected_mtcrs), 1):
            args = (idx, total, apk, mtcr, output_base, reverse)
            result = apply_patch_worker(args)
            _, apk, mtcr, out, ok, msg = result
            
            progress.update()
            
            if ok:
                success_count += 1
                add_to_history("apks", apk)
                add_to_history("mtcrs", mtcr)
                add_to_history("outputs", out)
            else:
                failed_items.append((idx, apk, mtcr, msg))
        
        progress.finish()

    # Summary
    print("\n" + "-" * 50)
    print_info(f"BATCH COMPLETE: {success_count}/{total} successful")
    
    if failed_items:
        print_error("Failed items:")
        for idx, apk, mtcr, msg in failed_items:
            print(f"  {idx}. {apk} + {mtcr}")
            print(f"     Reason: {msg}")
    
    print_info(f"Output directory: {output_base}")
    print("-" * 50)
    
    logging.info(f"BATCH: {success_count}/{total} success, output: {output_base}")

# ----------------- CLI Mode -----------------
def apply_single_cli(args):
    """CLI mode execution"""
    if not check_disk_space(silent=True):
        return False
        
    if not check_jar():
        return False
    
    # Validate inputs
    valid, msg = validate_apk(args.apk)
    if not valid:
        print_error(f"APK invalid: {msg}")
        return False
    
    valid, msg = validate_mtcr(args.mtcr)
    if not valid:
        print_error(f"MTCR invalid: {msg}")
        return False
    
    output = args.output or auto_output_name()
    
    if not confirm_overwrite(output):
        return False
    
    print_info(f"Output: {output}")
    
    backup_path = create_backup(args.apk)
    
    spinner = Spinner("Applying patch...")
    spinner.start()
    
    success, message = run_patch_command(args.apk, args.mtcr, output, args.reverse)
    
    spinner.stop()
    
    if success:
        print_success(f"Success: {output}")
        add_to_history("apks", args.apk)
        add_to_history("mtcrs", args.mtcr)
        add_to_history("outputs", output)
        
        if backup_path and Path(backup_path).exists():
            Path(backup_path).unlink()
            
        logging.info(f"CLI SUCCESS: {args.apk} + {args.mtcr} -> {output}")
        return True
    else:
        print_error(f"Failed: {message}")
        if backup_path:
            restore_backup(backup_path, args.apk)
        logging.error(f"CLI FAILED: {args.apk} + {args.mtcr} | {message}")
        return False

# ----------------- Menu Functions -----------------
def show_about():
    clear_screen()
    print_banner_text("ABOUT MTCR APPLY TOOL")
    print()
    print(f"  Version:    {__version__}")
    print(f"  Author:     {__author__}")
    print(f"  License:    {__license__}")
    print(f"  Repository: {__repository__}")
    print()
    print("FEATURES:")
    print("  • Single & batch patching modes")
    print("  • Parallel processing support")
    print("  • Automatic backup & restore")
    print("  • File integrity validation")
    print("  • Progress tracking")
    print("  • Session history")
    print("  • Colored terminal output")
    print()
    print("REQUIREMENTS:")
    print("  • Python 3.7+")
    print("  • Java 17+ (OpenJDK)")
    print("  • mtcr-apply.jar")
    print("  • 500MB+ free storage")
    print()
    input("Press Enter to return...")

def view_log():
    clear_screen()
    print_banner_text("RECENT ACTIVITY")
    print()
    
    log_file = CONFIG.get("log_file", "mtcr_apply.log")
    if Path(log_file).exists():
        try:
            with open(log_file, "r") as f:
                lines = f.readlines()
                # Show last 20 lines, filter by level if needed
                for line in lines[-20:]:
                    line = line.strip()
                    if "[ERROR]" in line:
                        print(colorize(line, Colors.RED))
                    elif "[WARNING]" in line:
                        print(colorize(line, Colors.YELLOW))
                    else:
                        print(line)
        except Exception as e:
            print_error(f"Cannot read log: {e}")
    else:
        print_info("No log file found")
    
    print()
    input("Press Enter to return...")

def manage_backups():
    """Backup management menu"""
    while True:
        clear_screen()
        print_banner_text("BACKUP MANAGEMENT")
        print()
        
        backups = list_backups()
        if not backups:
            print_info("No backups found")
            input("\nPress Enter to return...")
            return
        
        print(f"Found {len(backups)} backup(s):")
        for i, b in enumerate(backups[:10], 1):
            size = os.path.getsize(b) / 1024 / 1024
            mtime = datetime.fromtimestamp(Path(b).stat().st_mtime)
            print(f"  {i}. {Path(b).name}")
            print(f"     Size: {size:.1f} MB | Date: {mtime.strftime('%Y-%m-%d %H:%M')}")
        
        print("\nOptions:")
        print("  1) Restore backup")
        print("  2) Delete backup")
        print("  3) Delete all backups")
        print("  4) Back")
        
        choice = input("\n[?] Choice: ").strip()
        
        if choice == "1":
            idx = input("Enter backup number: ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(backups):
                target = input("Enter target APK path: ").strip()
                if restore_backup(backups[int(idx)-1], target):
                    print_success("Restored successfully")
                input("Press Enter to continue...")
        
        elif choice == "2":
            idx = input("Enter backup number: ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(backups):
                try:
                    Path(backups[int(idx)-1]).unlink()
                    # Also delete metadata
                    meta = Path(backups[int(idx)-1]).with_suffix('.json')
                    if meta.exists():
                        meta.unlink()
                    print_success("Deleted")
                except Exception as e:
                    print_error(f"Delete failed: {e}")
                input("Press Enter to continue...")
        
        elif choice == "3":
            if input("Delete ALL backups? [yes/N]: ").lower() == 'yes':
                for b in backups:
                    try:
                        Path(b).unlink()
                        meta = Path(b).with_suffix('.json')
                        if meta.exists():
                            meta.unlink()
                    except:
                        pass
                print_success("All backups deleted")
            input("Press Enter to continue...")
        
        elif choice == "4":
            break

def settings_menu():
    """Interactive settings"""
    global CONFIG, VERBOSE, DRY_RUN
    
    while True:
        clear_screen()
        print_banner_text("SETTINGS")
        print()
        
        settings = [
            ("Backup enabled", "backup_enabled", bool),
            ("Max retries", "max_retries", int),
            ("Timeout (seconds)", "timeout", int),
            ("Max workers", "max_workers", int),
            ("Min free space (MB)", "min_free_space_mb", int),
            ("Use colors", "use_colors", bool),
            ("Verbose mode", "verbose_mode", bool),
            ("Save history", "save_history", bool),
            ("Auto clean temp", "auto_clean_temp", bool),
        ]
        
        for i, (label, key, type_) in enumerate(settings, 1):
            val = CONFIG.get(key, DEFAULT_CONFIG.get(key))
            marker = "✓" if val else "✗" if isinstance(val, bool) else str(val)
            print(f"  {i}) {label:<25} [{marker}]")
        
        print(f"\n  S) Save configuration")
        print(f"  R) Reset to defaults")
        print(f"  B) Back to main menu")
        
        choice = input("\n[?] Choice: ").strip().lower()
        
        if choice == 's':
            if save_config():
                print_success("Configuration saved!")
                # Reload globals
                VERBOSE = CONFIG.get("verbose_mode", False)
                setup_logging()
            else:
                print_error("Save failed")
            input("Press Enter to continue...")
        
        elif choice == 'r':
            CONFIG = DEFAULT_CONFIG.copy()
            print_success("Reset to defaults")
            input("Press Enter to continue...")
        
        elif choice == 'b':
            break
        
        elif choice.isdigit() and 1 <= int(choice) <= len(settings):
            idx = int(choice) - 1
            label, key, type_ = settings[idx]
            
            if type_ == bool:
                CONFIG[key] = not CONFIG.get(key, DEFAULT_CONFIG.get(key))
            else:
                current = CONFIG.get(key, DEFAULT_CONFIG.get(key))
                new_val = input(f"Enter new value for {label} (current: {current}): ").strip()
                try:
                    CONFIG[key] = type_(new_val)
                except:
                    print_error("Invalid value")

def quick_scan():
    """Quick directory scan"""
    clear_screen()
    print_banner_text("DIRECTORY SCAN")
    print()
    
    apks, mtcrs = scan_directory()
    
    print(f"APK files found: {len(apks)}")
    for f in apks[:5]:
        size = os.path.getsize(f) / 1024 / 1024
        print(f"  • {f} ({size:.1f} MB)")
    if len(apks) > 5:
        print(f"  ... and {len(apks) - 5} more")
    
    print(f"\nMTCR files found: {len(mtcrs)}")
    for f in mtcrs[:5]:
        size = os.path.getsize(f) / 1024
        print(f"  • {f} ({size:.1f} KB)")
    if len(mtcrs) > 5:
        print(f"  ... and {len(mtcrs) - 5} more")
    
    print()
    input("Press Enter to return...")

def main_menu():
    """Main interactive menu — MMK MODS style"""
    while True:
        clear_screen()
        mtcr_banner()
        
        apks, mtcrs = scan_directory()
        print(f"  {C.DIM}APKs: {C.CYAN}{len(apks)}{C.RESET}{C.DIM}  │  MTCRs: {C.CYAN}{len(mtcrs)}{C.RESET}{C.DIM}  │  Backups: {C.CYAN}{len(list_backups())}{C.RESET}")
        print()
        print(f"  {C.BOLD}{C.CYAN}▶ PATCH{C.RESET}")
        print(f"     {C.GREEN}1){C.RESET}  Single patch          {C.DIM}(1 APK + 1 MTCR){C.RESET}")
        print(f"     {C.GREEN}2){C.RESET}  Single reverse patch")
        print(f"     {C.GREEN}3){C.RESET}  Batch patch            {C.DIM}(sequential){C.RESET}")
        print(f"     {C.GREEN}4){C.RESET}  Batch patch            {C.DIM}(parallel){C.RESET}")
        print(f"     {C.GREEN}5){C.RESET}  Batch reverse patch")
        print()
        print(f"  {C.BOLD}{C.MAGENTA}▶ TOOLS{C.RESET}")
        print(f"     {C.GREEN}6){C.RESET}  Quick scan")
        print(f"     {C.GREEN}7){C.RESET}  Manage backups")
        print(f"     {C.GREEN}8){C.RESET}  View log")
        print(f"     {C.GREEN}9){C.RESET}  Settings")
        print(f"    {C.GREEN}10){C.RESET}  About")
        print()
        print(f"  {C.DIM}────────────────────────────────────{C.RESET}")
        print(f"     {C.RED}0){C.RESET}  Back to MMK MODS")
        print()
        
        choice = input(f"  {C.MAGENTA}𝙿𝚒𝚕𝚒𝚑 𝚗𝚘𝚖𝚘𝚛 ➤{C.RESET} ").strip()
        
        if choice == "0":
            print_info("Returning to MMK MODS menu...")
            if CONFIG.get("auto_clean_temp", True):
                cleanup_temp()
            return
        elif choice == "1":
            apply_single(False)
            input("\nPress Enter to continue...")
        elif choice == "2":
            apply_single(True)
            input("\nPress Enter to continue...")
        elif choice == "3":
            apply_paired(False, parallel=False)
            input("\nPress Enter to continue...")
        elif choice == "4":
            apply_paired(False, parallel=True)
            input("\nPress Enter to continue...")
        elif choice == "5":
            apply_paired(True, parallel=False)
            input("\nPress Enter to continue...")
        elif choice == "6":
            quick_scan()
        elif choice == "7":
            manage_backups()
        elif choice == "8":
            view_log()
        elif choice == "9":
            settings_menu()
        elif choice == "10":
            show_about()
        else:
            print_error("Invalid choice")

# ----------------- Argument Parser -----------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="MTCR Apply Tool - Professional APK Patching Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Interactive mode
  %(prog)s -a app.apk -m fix.mtcr   # Quick patch
  %(prog)s -a app.apk -m fix.mtcr -r # Reverse patch
  %(prog)s --dry-run -a app.apk -m fix.mtcr  # Simulate only
        """
    )
    
    parser.add_argument("-a", "--apk", help="APK file path")
    parser.add_argument("-m", "--mtcr", help="MTCR patch file")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("-r", "--reverse", action="store_true", help="Reverse patch")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without executing")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--no-color", action="store_true", help="Disable colors")
    parser.add_argument("-c", "--config", help="Config file path")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    
    return parser.parse_args()

# ----------------- Main Entry -----------------




# ═══════════════════════════════════════════════════════════════
#  SECTION: NEXUS CLOUD TOOLKIT  (MMK MODS unified UI)
# ═══════════════════════════════════════════════════════════════

try:
    import requests as _nexus_requests
except ImportError:
    _nexus_requests = None

NEXUS_API_KEY = "paul87-c4ed400d-8ed2-4842-9a67-52e8107e6660"
NEXUS_BASE_URL = "https://api.revengi.in"


class NexusCloudTerminal:
    def __init__(self):
        self.headers = {"X-API-Key": NEXUS_API_KEY}
        self.work_dir = "nexus_temp"
        if not os.path.exists(self.work_dir):
            os.makedirs(self.work_dir)
        if _nexus_requests is None:
            spinner("Installing requests...", 1.0)
            os.system(f"{sys.executable} -m pip install requests -q")

    def clear(self):
        os.system("clear" if os.name != "nt" else "cls")

    def banner(self):
        self.clear()
        logo = [
            r"  ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗",
            r"  ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝",
            r"  ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗",
            r"  ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║",
            r"  ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████╗",
            r"  ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝",
        ]
        print()
        for line in logo:
            print(f"{C.CYAN}{line}{C.RESET}")
        print(f"{C.MAGENTA}{'═'*52}{C.RESET}")
        print(f"{C.BOLD}{C.WHITE}  NEXUS CLOUD TOOLKIT  •  MMK MODS{C.RESET}")
        print(f"{C.DIM}  Cloud reverse engineering  ·  Blutter / JNI / DEX{C.RESET}")
        print(f"{C.MAGENTA}{'═'*52}{C.RESET}")
        print()

    def get_file_size(self, path):
        if not os.path.exists(path):
            return "0 B"
        return human_size(os.path.getsize(path))

    def create_lite_apk(self, original_apk):
        if not os.path.exists(self.work_dir):
            os.makedirs(self.work_dir)
        lite_name = os.path.join(self.work_dir, "lite_upload.apk")
        banner("SMART COMPRESS", "strip assets → lite APK")
        spinner("Filtering dex / so / manifest...", 1.0)
        try:
            with zipfile.ZipFile(original_apk, 'r') as zin:
                members = zin.infolist()
                kept = 0
                with zipfile.ZipFile(lite_name, 'w', zipfile.ZIP_DEFLATED) as zout:
                    for i, item in enumerate(members, 1):
                        fname = item.filename
                        if fname.endswith((".dex", ".arsc", ".xml", ".so")) or \
                           fname.startswith("lib/") or \
                           fname == "AndroidManifest.xml":
                            zout.writestr(item, zin.read(fname))
                            kept += 1
                        if i % 50 == 0 or i == len(members):
                            progress_bar(i, len(members), "compress")
            old_size = os.path.getsize(original_apk) / (1024 * 1024)
            new_size = os.path.getsize(lite_name) / (1024 * 1024)
            ok(f"Compressed: {old_size:.1f} MB → {new_size:.1f} MB ({kept} entries)")
            return lite_name
        except Exception as e:
            err(f"Compression failed: {e}")
            return original_apk

    def select_file(self, extension, label):
        files = sorted([f for f in os.listdir('.') if f.endswith(extension)])
        if not files:
            err(f"No {label} files found")
            input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
            return None
        entries = []
        for f in files:
            try:
                sz = os.path.getsize(f)
            except OSError:
                sz = 0
            entries.append((os.path.abspath(f), f, sz))
        if 'select_target' in globals():
            chosen = select_target(entries, title=f"SELECT TARGET  •  {label}")
            return os.path.basename(chosen) if chosen else None
        # fallback
        banner(f"SELECT {label}", f"{len(files)} file(s)")
        for i, f in enumerate(files, 1):
            print(f"  {C.GREEN}{i:2d}{C.RESET}  {f:<40} {C.CYAN}{self.get_file_size(f):>10}{C.RESET}")
        print(f"  {C.RED} 0{C.RESET}  BACK")
        try:
            c = input(f"\n{C.MAGENTA}𝙿𝚒𝚕𝚒𝚑 𝚗𝚘𝚖𝚘𝚛 ➤{C.RESET} ").strip()
            if c == "0":
                return None
            idx = int(c)
            if 1 <= idx <= len(files):
                return files[idx - 1]
        except Exception:
            pass
        return None

    def extract_so_from_apk(self, apk_path):
        if not os.path.exists(self.work_dir):
            os.makedirs(self.work_dir)
        banner("EXTRACT NATIVE LIBS", "libapp.so + libflutter.so")
        spinner("Scanning APK...", 0.8)
        target_archs = ["arm64-v8a", "armeabi-v7a"]
        try:
            with zipfile.ZipFile(apk_path, 'r') as z:
                all_files = z.namelist()
                lib_app_path = None
                lib_flu_path = None
                for arch in target_archs:
                    if not lib_app_path:
                        lib_app_path = next((x for x in all_files if f"lib/{arch}/libapp.so" in x), None)
                    if not lib_flu_path:
                        lib_flu_path = next((x for x in all_files if f"lib/{arch}/libflutter.so" in x), None)
                if not lib_app_path:
                    lib_app_path = next((x for x in all_files if "libapp.so" in x), None)
                if not lib_flu_path:
                    lib_flu_path = next((x for x in all_files if "libflutter.so" in x), None)
                if not lib_app_path or not lib_flu_path:
                    err("libapp.so or libflutter.so not found")
                    return None
                spinner("Extracting .so files...", 0.8)
                p1 = z.extract(lib_app_path, self.work_dir)
                p2 = z.extract(lib_flu_path, self.work_dir)
                ok(f"Extracted: {os.path.basename(p1)} & {os.path.basename(p2)}")
                return {'libapp': open(p1, 'rb'), 'libflutter': open(p2, 'rb')}
        except Exception as e:
            err(f"Extraction error: {e}")
            return None

    def execute_request(self, endpoint, tag, files_dict):
        import requests
        url = f"{NEXUS_BASE_URL}/{endpoint}"
        banner("NEXUS CLOUD", f"POST /{endpoint}")
        spinner(f"Uploading ({tag.upper()}) — tunggu response...", 2.0)
        print(f"  {C.DIM}│  timeout 600s  ·  cloud processing...{C.RESET}")
        try:
            res = requests.post(url, headers=self.headers, files=files_dict, timeout=600)
            if res.status_code == 200:
                spinner("Saving response...", 0.6)
                ctype = res.headers.get('Content-Type', '')
                ext = ".zip"
                if 'json' in ctype:
                    ext = ".json"
                if tag == "repair":
                    ext = ".dex"
                if tag == "merge":
                    ext = ".apk"
                filename = f"NEXUS_{tag.upper()}_{int(time.time())}{ext}"
                with open(filename, "wb") as f:
                    f.write(res.content)
                ok(f"Saved: {filename} ({human_size(len(res.content))})")
                return True, filename, f"HTTP {res.status_code}"
            error_msg = res.text
            if len(error_msg) > 120:
                error_msg = error_msg[:120] + "..."
            return False, None, f"HTTP {res.status_code}: {error_msg}"
        except requests.exceptions.Timeout:
            return False, None, "Timeout — file terlalu besar / jaringan lambat"
        except Exception as e:
            return False, None, str(e)

    def nexus_main_menu(self):
        while True:
            self.banner()
            print(f"  {C.BOLD}{C.CYAN}▶ ANALYSIS{C.RESET}")
            print(f"     {C.GREEN}1){C.RESET}  JNI Analysis (APK)")
            print(f"     {C.GREEN}2){C.RESET}  Flutter Analysis (APK)")
            print(f"     {C.GREEN}3){C.RESET}  Blutter Engine (APK)   {C.DIM}[cloud]{C.RESET}")
            print(f"     {C.GREEN}4){C.RESET}  MT Hook Gen (APK)")
            print()
            print(f"  {C.BOLD}{C.MAGENTA}▶ UTILS{C.RESET}")
            print(f"     {C.GREEN}5){C.RESET}  Dex Repair")
            print(f"     {C.GREEN}6){C.RESET}  APKS → APK (merge)")
            print(f"     {C.GREEN}7){C.RESET}  Py-Fuscate            {C.DIM}[encode / decode]{C.RESET}")
            print(f"     {C.GREEN}8){C.RESET}  Find Offset           {C.DIM}[libapp.so → true]{C.RESET}")
            print(f"     {C.GREEN}9){C.RESET}  Sign APK              {C.DIM}[.jks / .keystore]{C.RESET}")
            print(f"    {C.GREEN}10){C.RESET}  Inject Dialog        {C.DIM}[dex + onCreate hook]{C.RESET}")
            print()
            print(f"  {C.DIM}────────────────────────────────────{C.RESET}")
            print(f"     {C.RED}0){C.RESET}  Back to MMK MODS")
            print()
            user_input = input(f"  {C.MAGENTA}𝙿𝚒𝚕𝚒𝚑 𝚗𝚘𝚖𝚘𝚛 ➤{C.RESET} ").strip()
            try:
                choice = int(user_input)
            except ValueError:
                warn("Masukkan angka")
                time.sleep(0.8)
                continue

            if choice == 0:
                info("Returning to MMK MODS...")
                break

            files_payload = None
            endpoint = ""
            tag = ""
            file_to_close = None

            if choice in (1, 4):
                target = self.select_file(".apk", "APK")
                if target:
                    size_mb = os.path.getsize(target) / (1024 * 1024)
                    file_to_upload = target
                    if size_mb > 45:
                        warn(f"File besar ({size_mb:.1f} MB)")
                        do = input(f"  {C.CYAN}Smart compress? [1=Yes / 0=Cancel] ➤{C.RESET} ").strip()
                        if do == "1":
                            file_to_upload = self.create_lite_apk(target)
                        else:
                            info("Upload cancelled")
                            input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
                            continue
                    endpoint = "analyze/jni" if choice == 1 else "mthook"
                    tag = "jni" if choice == 1 else "hook"
                    file_obj = open(file_to_upload, 'rb')
                    files_payload = {'apk_file': file_obj}
                    file_to_close = file_obj

            elif choice in (2, 3):
                target = self.select_file(".apk", "APK")
                if target:
                    extracted = self.extract_so_from_apk(target)
                    if extracted:
                        files_payload = extracted
                        endpoint = "analyze/flutter" if choice == 2 else "blutter"
                        tag = "flutter" if choice == 2 else "blutter"

            elif choice == 5:
                target = self.select_file(".dex", "DEX")
                if target:
                    endpoint = "dex-repair"
                    tag = "repair"
                    file_obj = open(target, 'rb')
                    files_payload = {'dex_file': file_obj}
                    file_to_close = file_obj

            elif choice == 6:
                target = self.select_file(".apks", "APKS")
                if target:
                    endpoint = "merge/apks"
                    tag = "merge"
                    size_mb = os.path.getsize(target) / (1024 * 1024)
                    if size_mb > 50:
                        warn(f"APKS besar ({size_mb:.1f} MB) — upload bisa lama")
                    file_obj = open(target, 'rb')
                    files_payload = {'apks_file': file_obj}
                    file_to_close = file_obj

            elif choice == 7:
                run_py_fuscate_interactive()
                continue

            elif choice == 8:
                run_find_offset_interactive()
                continue

            elif choice == 9:
                run_sign_apk_interactive()
                continue

            elif choice == 10:
                run_inject_dex_hook_interactive()
                continue

            if files_payload and endpoint:
                success, fname, msg = self.execute_request(endpoint, tag, files_payload)
                if file_to_close:
                    try:
                        file_to_close.close()
                    except Exception:
                        pass
                if isinstance(files_payload, dict):
                    for k, v in files_payload.items():
                        try:
                            v.close()
                        except Exception:
                            pass
                lite_path = os.path.join(self.work_dir, "lite_upload.apk")
                if os.path.exists(lite_path):
                    try:
                        os.remove(lite_path)
                    except Exception:
                        pass
                print()
                if success:
                    print(f"  {C.MAGENTA}╔{'═'*48}╗{C.RESET}")
                    print(f"  {C.MAGENTA}║{C.RESET}{C.BOLD}{C.GREEN}{'SUCCESS'.center(48)}{C.RESET}{C.MAGENTA}║{C.RESET}")
                    print(f"  {C.MAGENTA}║{C.RESET}  Output: {C.CYAN}{fname}{C.RESET}")
                    print(f"  {C.MAGENTA}║{C.RESET}  {C.DIM}{msg}{C.RESET}")
                    print(f"  {C.MAGENTA}╚{'═'*48}╝{C.RESET}")
                else:
                    print(f"  {C.RED}╔{'═'*48}╗{C.RESET}")
                    print(f"  {C.RED}║{C.RESET}{C.BOLD}{'FAILED'.center(48)}{C.RESET}{C.RED}║{C.RESET}")
                    print(f"  {C.RED}║{C.RESET}  {msg[:60]}")
                    print(f"  {C.RED}╚{'═'*48}╝{C.RESET}")
                input(f"\n{C.YELLOW}Press Enter...{C.RESET}")




# ─── Py-Fuscate (Toolkit option 7) ─────────────────────────────
import marshal as _marshal
import lzma as _lzma
import gzip as _gzip
import bz2 as _bz2
import binascii as _binascii
import zlib as _zlib
import random as _random


def _pyfuscate_encode_once(source: str) -> str:
    selected_mode = _random.choice((_lzma, _gzip, _bz2, _binascii, _zlib))
    marshal_encoded = _marshal.dumps(compile(source, "Py-Fuscate", "exec"))
    if selected_mode is _binascii:
        return (
            "import marshal,lzma,gzip,bz2,binascii,zlib;"
            "exec(marshal.loads(binascii.a2b_base64({})))".format(
                _binascii.b2a_base64(marshal_encoded)
            )
        )
    return (
        "import marshal,lzma,gzip,bz2,binascii,zlib;"
        "exec(marshal.loads({}.decompress({})))".format(
            selected_mode.__name__, selected_mode.compress(marshal_encoded)
        )
    )


def _pyfuscate_try_decompile(code_obj):
    """Coba decompile code object → source (butuh decompyle3/uncompyle6)."""
    # decompyle3
    try:
        from decompyle3.main import decompile
        import io
        buf = io.StringIO()
        decompile(code_obj, out=buf)
        src = buf.getvalue()
        if src.strip():
            return src
    except Exception:
        pass
    # uncompyle6
    try:
        import uncompyle6
        import io
        buf = io.StringIO()
        uncompyle6.uncompyle_code(code_obj, out=buf)
        src = buf.getvalue()
        if src.strip():
            return src
    except Exception:
        pass
    # xdis + manual fallback: show disassembly note
    return None


def _pyfuscate_unwrap_once(source: str):
    """
    Buka 1 lapisan wrapper:
      exec(marshal.loads(MOD.decompress(BYTES)))
      exec(marshal.loads(binascii.a2b_base64(BYTES)))
    Return (ok, next_source_or_None, code_obj_or_None, msg)
    """
    import ast

    s = source.strip()
    # strip try/except wrapper header
    if "try:" in s and "exec(" in s:
        # ambil isi exec(...)
        m = re.search(r"exec\((.*)\)\s*(?:\n|$)", s, re.DOTALL)
        if m:
            s = "exec(" + m.group(1) + ")"

    # Pattern: marshal.loads(NAME.decompress(PAYLOAD))
    m = re.search(
        r"marshal\.loads\(\s*(lzma|gzip|bz2|zlib)\.decompress\(\s*(.+)\s*\)\s*\)",
        s,
        re.DOTALL,
    )
    if m:
        mod_name, payload_expr = m.group(1), m.group(2).strip()
        try:
            payload = ast.literal_eval(payload_expr)
            if not isinstance(payload, (bytes, bytearray)):
                return False, None, None, "payload bukan bytes"
            mod = {"lzma": _lzma, "gzip": _gzip, "bz2": _bz2, "zlib": _zlib}[mod_name]
            raw = mod.decompress(payload)
            code_obj = _marshal.loads(raw)
            src = _pyfuscate_try_decompile(code_obj)
            return True, src, code_obj, mod_name
        except Exception as e:
            return False, None, None, str(e)

    # Pattern: marshal.loads(binascii.a2b_base64(PAYLOAD))
    m = re.search(
        r"marshal\.loads\(\s*binascii\.a2b_base64\(\s*(.+)\s*\)\s*\)",
        s,
        re.DOTALL,
    )
    if m:
        payload_expr = m.group(1).strip()
        try:
            payload = ast.literal_eval(payload_expr)
            raw = _binascii.a2b_base64(payload)
            code_obj = _marshal.loads(raw)
            src = _pyfuscate_try_decompile(code_obj)
            return True, src, code_obj, "binascii"
        except Exception as e:
            return False, None, None, str(e)

    return False, None, None, "bukan format Py-Fuscate / MMK MOD"


def run_py_fuscate_interactive():
    """Interactive Py-Fuscate — Encode (lindungi) / Decode (buka pelindung)"""
    banner("PY-FUSCATE", "MMK MOD  •  encode / decode")
    print()
    print(f"  {C.BOLD}{C.CYAN}▶ MODE{C.RESET}")
    print(f"     {C.GREEN}1){C.RESET}  Encode   {C.DIM}— melindungi (obfuscate){C.RESET}")
    print(f"     {C.GREEN}2){C.RESET}  Decode   {C.DIM}— buka pelindung{C.RESET}")
    print(f"     {C.RED}0){C.RESET}  Back")
    print()
    mode = input(f"  {C.MAGENTA}𝙿𝚒𝚕𝚒𝚑 𝚗𝚘𝚖𝚘𝚛 ➤{C.RESET} ").strip()
    if mode == "0" or mode == "":
        return
    if mode == "1":
        _pyfuscate_do_encode()
    elif mode == "2":
        _pyfuscate_do_decode()
    else:
        warn("Pilihan tidak valid")
        input(f"\n{C.YELLOW}Press Enter...{C.RESET}")


def _pyfuscate_pick_py(include_enc=True, exclude_enc=False):
    skip = {"mmk_mods.py", "mmk_mods_all.py", "inject_dialog_mmk.py"}
    py_files = []
    for f in sorted(os.listdir(".")):
        if not f.endswith(".py") or not os.path.isfile(f) or f.startswith("."):
            continue
        if f in skip:
            continue
        if exclude_enc and (f.endswith("-enc.py") or f.endswith("_enc.py")):
            continue
        py_files.append(f)
    if not include_enc:
        py_files = [f for f in py_files if not (f.endswith("-enc.py") or f.endswith("_enc.py"))]
    if not py_files:
        return None, None
    entries = []
    for f in py_files:
        try:
            sz = os.path.getsize(f)
        except OSError:
            sz = 0
        entries.append((os.path.abspath(f), f, sz))
    if "select_target" in globals():
        chosen = select_target(entries, title="SELECT TARGET  •  .PY FILE")
        if not chosen:
            return None, None
        return chosen, os.path.basename(chosen)
    for i, f in enumerate(py_files, 1):
        print(f"  {C.GREEN}{i:2d}{C.RESET}  {f}")
    try:
        idx = int(input(f"\n{C.MAGENTA}➤{C.RESET} ").strip())
        name = py_files[idx - 1]
        return os.path.abspath(name), name
    except Exception:
        return None, None


def _pyfuscate_do_encode():
    banner("ENCODE", "melindungi source  •  marshal + compress")
    info("Setara CLI: python py_fuscate.py -i in.py -o out-enc.py -c 50")
    print()

    input_path, input_name = _pyfuscate_pick_py(exclude_enc=True)
    if not input_path:
        err("Tidak ada file .py / dibatalkan")
        input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
        return

    ok(f"Target: {input_name}")
    stem = Path(input_name).stem
    default_out = f"{stem}-enc.py"
    print()
    out_name = input(
        f"  {C.CYAN}Output{C.RESET} [{C.DIM}{default_out}{C.RESET}] ➤ "
    ).strip() or default_out
    if not out_name.endswith(".py"):
        out_name += ".py"

    print()
    print(f"  {C.DIM}50=cepat  ·  100=disarankan  ·  500–1000=sangat lambat{C.RESET}")
    while True:
        level_s = input(f"  {C.CYAN}Levels [50 ~ 1000]{C.RESET} ➤ ").strip() or "100"
        try:
            level = int(level_s)
            if 50 <= level <= 1000:
                break
            warn("50–1000 saja")
        except ValueError:
            warn("Angka saja")

    print()
    print(f"  {C.DIM}│ input  : {input_name}{C.RESET}")
    print(f"  {C.DIM}│ output : {out_name}{C.RESET}")
    print(f"  {C.DIM}│ levels : {level}{C.RESET}")
    conf = input(f"\n  {C.YELLOW}Lanjut encode (lindungi)? [y/N]{C.RESET} ➤ ").strip().lower()
    if conf not in ("y", "yes", "ya", "1"):
        info("Dibatalkan")
        return

    try:
        with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception as e:
        err(f"Gagal baca: {e}")
        return
    if not source.strip():
        err("File kosong")
        return

    banner("ENCODING", f"{input_name} → {out_name}  c={level}")
    spinner(f"{level} layers...", 0.4)
    try:
        encoded = source
        for i in range(level):
            encoded = _pyfuscate_encode_once(encoded)
            if (i + 1) % max(1, level // 20) == 0 or (i + 1) == level:
                progress_bar(i + 1, level, "encode")
    except Exception as e:
        err(f"Encode error: {e}")
        return

    py_ver = "python" + ".".join(str(x) for x in sys.version_info[:2])
    header = (
        f"# Encoded By MMK MOD\n"
        f"# Mode: ENCODE (protected)\n"
        f"# https://whatsapp.com/channel/0029Vb7vQrL1yT22MFrBrR42\n"
        f"# Run with {py_ver}\n"
        f"try:\n\t{encoded}\nexcept KeyboardInterrupt:\n\texit()\n"
    )
    with open(out_name, "w", encoding="utf-8") as f:
        f.write(header)
    ok(f"Saved: {out_name} ({human_size(os.path.getsize(out_name))})")
    print()
    print(f"  {C.MAGENTA}╔{'═'*48}╗{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}{C.BOLD}{C.GREEN}{'ENCODE DONE — TERLINDUNGI'.center(48)}{C.RESET}{C.MAGENTA}║{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  Out: {C.CYAN}{out_name}{C.RESET}  levels={level}")
    print(f"  {C.MAGENTA}╚{'═'*48}╝{C.RESET}")
    input(f"\n{C.YELLOW}Press Enter...{C.RESET}")


def _pyfuscate_do_decode():
    banner("DECODE", "buka pelindung  •  unwrap marshal layers")
    info("Butuh file hasil encode MMK MOD / Py-Fuscate")
    info("Decompile penuh: pip install decompyle3  (opsional, disarankan)")
    print()

    input_path, input_name = _pyfuscate_pick_py(include_enc=True)
    if not input_path:
        err("Tidak ada file .py / dibatalkan")
        input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
        return

    ok(f"Target: {input_name}")
    stem = Path(input_name).stem
    if stem.endswith("-enc"):
        stem = stem[:-4]
    default_out = f"{stem}-decoded.py"
    print()
    out_name = input(
        f"  {C.CYAN}Output{C.RESET} [{C.DIM}{default_out}{C.RESET}] ➤ "
    ).strip() or default_out
    if not out_name.endswith(".py"):
        out_name += ".py"

    max_layers = 1000
    print()
    ml = input(f"  {C.CYAN}Max layers buka{C.RESET} [{C.DIM}{max_layers}{C.RESET}] ➤ ").strip()
    if ml.isdigit():
        max_layers = max(1, min(int(ml), 5000))

    conf = input(f"\n  {C.YELLOW}Lanjut decode (buka pelindung)? [y/N]{C.RESET} ➤ ").strip().lower()
    if conf not in ("y", "yes", "ya", "1"):
        info("Dibatalkan")
        return

    try:
        with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
            current = f.read()
    except Exception as e:
        err(f"Gagal baca: {e}")
        return

    banner("DECODING", f"{input_name} → {out_name}")
    layers_done = 0
    last_code = None

    for i in range(max_layers):
        ok_u, src, code_obj, msg = _pyfuscate_unwrap_once(current)
        if not ok_u:
            if layers_done == 0:
                err(f"Bukan format terenkripsi / gagal unwrap: {msg}")
                info("Pastikan file di-encode oleh MMK MOD Py-Fuscate")
                input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
                return
            info(f"Berhenti di layer {layers_done}: {msg}")
            break
        layers_done += 1
        last_code = code_obj
        if src:
            current = src
            if (layers_done % 5 == 0) or layers_done == 1:
                progress_bar(layers_done, max(layers_done, 20), f"decode layer")
            # jika source sudah tidak mengandung marshal.loads, selesai
            if "marshal.loads" not in src and "exec(" not in src[:200]:
                ok(f"Source terbuka setelah {layers_done} layer")
                break
        else:
            # tidak ada decompiler — simpan disassembly
            warn(f"Layer {layers_done}: payload OK tapi decompiler tidak ada")
            info("Install: pip install decompyle3")
            break

    # tulis hasil
    if "marshal.loads" not in current or layers_done > 0:
        header = (
            f"# Decoded By MMK MOD\n"
            f"# Source: {input_name}\n"
            f"# Layers unwrapped: {layers_done}\n"
            f"# ================================\n\n"
        )
        body = current
        if last_code is not None and ("marshal.loads" in current or not current.strip()):
            # fallback: tulis dis sebagai komentar + note
            import dis
            import io
            buf = io.StringIO()
            try:
                dis.dis(last_code, file=buf)
                body = (
                    f"# [!] Source tidak bisa di-decompile otomatis.\n"
                    f"#     Install decompyle3 lalu decode lagi.\n"
                    f"#     Disassembly layer terakhir:\n#\n"
                    + "\n".join("# " + ln for ln in buf.getvalue().splitlines())
                    + "\n"
                )
            except Exception:
                body = current
        try:
            with open(out_name, "w", encoding="utf-8") as f:
                f.write(header + body)
            ok(f"Saved: {out_name} ({human_size(os.path.getsize(out_name))})")
        except Exception as e:
            err(f"Gagal tulis: {e}")
            return

    print()
    print(f"  {C.MAGENTA}╔{'═'*48}╗{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}{C.BOLD}{C.GREEN}{'DECODE DONE — PELINDUNG DIBUKA'.center(48)}{C.RESET}{C.MAGENTA}║{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  Out   : {C.CYAN}{out_name}{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  Layers: {layers_done}")
    print(f"  {C.MAGENTA}╚{'═'*48}╝{C.RESET}")
    input(f"\n{C.YELLOW}Press Enter...{C.RESET}")



def _locate_libapp_so():
    """Cari libapp.so di folder kerja / subfolder umum."""
    candidates = []
    cwd = Path(".")
    # direct
    for p in [
        cwd / "libapp.so",
        cwd / "arm64-v8a" / "libapp.so",
        cwd / "lib" / "arm64-v8a" / "libapp.so",
        cwd / "libapp" / "libapp.so",
    ]:
        if p.is_file():
            candidates.append(p.resolve())
    # scan shallow
    for p in cwd.rglob("libapp.so"):
        try:
            if p.is_file() and p.resolve() not in candidates:
                # limit depth noise
                if len(p.parts) <= 4:
                    candidates.append(p.resolve())
        except Exception:
            pass
    # unique
    seen = set()
    out = []
    for c in candidates:
        s = str(c)
        if s not in seen:
            seen.add(s)
            out.append(c)
    return out


def run_find_offset_interactive():
    """
    Toolkit → Find Offset
    - Cari libapp.so
    - Blutter + regex keyword Flutter (sama seperti Flutter patcher)
    - Tampilkan offset yang ketemu
    - Tanya: Atur semua ke true?
        Ya  → patch false → true (semua)
        Tidak → hentikan sesi
    """
    banner("FIND OFFSET", "libapp.so  •  keyword Flutter  •  false → true")
    info("Keyword: premium / vip / subscription / isPro / ...")
    print()

    lib_list = _locate_libapp_so()
    lib_path = None

    if lib_list:
        entries = [(str(p), str(p.relative_to(Path('.').resolve()) if str(p).startswith(str(Path('.').resolve())) else p.name), p.stat().st_size) for p in lib_list]
        # fix display names
        entries = []
        for p in lib_list:
            try:
                rel = os.path.relpath(str(p), os.getcwd())
            except Exception:
                rel = p.name
            entries.append((str(p), rel, p.stat().st_size))
        if "select_target" in globals():
            chosen = select_target(entries, title="SELECT TARGET  •  libapp.so")
            if not chosen:
                info("Dibatalkan")
                return
            lib_path = chosen
        else:
            lib_path = str(lib_list[0])
            ok(f"Auto: {lib_path}")
    else:
        # coba dari APK
        warn("libapp.so tidak ketemu di folder")
        info("Coba extract dari APK...")
        entries = mmk_list_apks((".apk", ".apks", ".xapk"))
        if not entries:
            err(f"Tidak ada libapp.so / APK di {MMK_APP_DIR}")
            info("Letakkan libapp.so atau APK Flutter di folder app/")
            input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
            return
        if "select_target" in globals():
            apk = select_target(entries, title="SELECT APK  •  extract libapp.so")
            if not apk:
                info("Dibatalkan")
                return
        else:
            apk = os.path.abspath(apks[0])
        try:
            spinner("Extract arm64-v8a / libapp.so...", 1.0)
            extract_arm64_folder_from_apk(apk, ".")
            if os.path.exists("libapp.so"):
                lib_path = os.path.abspath("libapp.so")
                ok(f"libapp.so → {lib_path}")
            else:
                err("Extract gagal: libapp.so tidak ada")
                input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
                return
        except Exception as e:
            err(f"Extract error: {e}")
            input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
            return

    if not lib_path or not os.path.exists(lib_path):
        err("libapp.so tidak valid")
        input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
        return

    ok(f"Target SO: {lib_path}")
    work = os.getcwd()

    # ── Siapkan struktur seperti Flutter patcher ──
    # Blutter butuh folder arm64-v8a/ yang berisi libapp.so
    arm64_dir = os.path.join(work, "arm64-v8a")
    arm64_lib = os.path.join(arm64_dir, "libapp.so")
    cwd_lib = os.path.join(work, "libapp.so")

    try:
        os.makedirs(arm64_dir, exist_ok=True)
        # salin libapp.so yang dipilih → arm64-v8a/libapp.so + ./libapp.so
        src = os.path.abspath(lib_path)
        if os.path.abspath(arm64_lib) != src:
            spinner("Menyiapkan arm64-v8a/libapp.so...", 0.6)
            shutil.copy2(src, arm64_lib)
            ok(f"arm64-v8a/libapp.so siap ({human_size(os.path.getsize(arm64_lib))})")
        if os.path.abspath(cwd_lib) != src and os.path.abspath(cwd_lib) != os.path.abspath(arm64_lib):
            shutil.copy2(src, cwd_lib)
        elif not os.path.exists(cwd_lib):
            shutil.copy2(arm64_lib, cwd_lib)
        lib_path = cwd_lib if os.path.exists(cwd_lib) else arm64_lib
        ok(f"Input Blutter: {arm64_dir}")
    except Exception as e:
        err(f"Gagal siapkan arm64-v8a: {e}")
        input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
        return

    # verifikasi libapp.so benar-benar ada di arm64-v8a
    if not os.path.isfile(arm64_lib) or os.path.getsize(arm64_lib) < 1024:
        err("arm64-v8a/libapp.so tidak valid / kosong")
        input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
        return

    # Blutter dump (sama seperti Flutter)
    base_name = "findoffset"
    try:
        spinner("Blutter dump (asm + pp.txt)...", 1.2)
        out_dir = run_blutter(base_name, work)
    except Exception as e:
        err(f"Blutter gagal: {e}")
        info("Pastikan ~/blutter-termux dan jaringan OK")
        info("Cek: ls arm64-v8a/libapp.so")
        input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
        return

    if not out_dir:
        err("Blutter tidak menghasilkan output")
        input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
        return

    asm_folder = os.path.join(out_dir, "asm")
    banner("SCAN KEYWORDS", "regex Flutter premium / vip / pro")
    try:
        matches = search_asm_folder(asm_folder)
    except Exception as e:
        err(f"Scan error: {e}")
        input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
        return

    if not matches:
        warn("Tidak ada match regex di asm/")
        input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
        return

    smngn_file = os.path.join(os.getcwd(), "smngn_findoffset.txt")
    create_smngn_file(matches, smngn_file)
    false_addresses = extract_false_addresses_from_smngn(smngn_file)

    print()
    banner("HASIL OFFSET", f"{len(false_addresses)} false address(es)")
    if not false_addresses:
        # tampilkan match addresses dari regex walau tidak ada literal false
        warn("Tidak ada pola 'false' eksplisit di smngn")
        info(f"Total regex matches: {len(matches)}")
        shown = 0
        for m in matches[:30]:
            addr = m.get("address", "?")
            print(f"  {C.YELLOW}◆{C.RESET} {C.CYAN}{addr}{C.RESET}  {C.DIM}{m.get('file','')[:40]}{C.RESET}")
            shown += 1
        if len(matches) > 30:
            info(f"... dan {len(matches)-30} lainnya (lihat smngn_findoffset.txt)")
        print()
        print(f"  {C.BOLD}Atur semua ke true?{C.RESET}")
        print(f"  {C.DIM}(Tidak ada false-pattern → patch ASM skip){C.RESET}")
        ans = input(f"  {C.MAGENTA}Ya / Tidak ➤{C.RESET} ").strip().lower()
        if ans in ("y", "ya", "yes", "1"):
            warn("Tidak ada alamat false yang bisa di-patch otomatis")
            info("Gunakan menu Flutter Patcher untuk full pipeline")
        else:
            info("Sesi dihentikan")
        input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
        return

    for i, item in enumerate(false_addresses, 1):
        if isinstance(item, dict):
            addr = item.get("address", "?")
            kw = item.get("keyword", "-")
        else:
            addr, kw = item, "-"
        print(f"  {C.GREEN}{i:3d}{C.RESET}  {C.CYAN}{addr}{C.RESET}  {C.YELLOW}{kw}{C.RESET}")
    print()
    ok(f"Total: {len(false_addresses)} offset")

    print()
    print(f"  {C.BOLD}{C.YELLOW}Atur semua ke true??{C.RESET}")
    print(f"  {C.DIM}Ya  = patch semua (false → true) via radare2{C.RESET}")
    print(f"  {C.DIM}Tidak = hentikan sesi{C.RESET}")
    ans = input(f"\n  {C.MAGENTA}Ya / Tidak ➤{C.RESET} ").strip().lower()

    if ans not in ("y", "ya", "yes", "1"):
        info("Sesi dihentikan — tidak ada perubahan pada libapp.so")
        input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
        return

    banner("PATCH ALL → TRUE", f"{len(false_addresses)} targets")
    try:
        results = patch_false_addresses(lib_path, false_addresses)
        success = sum(1 for r in results.values() if r.get("patched"))
        ok(f"Patched: {success}/{len(false_addresses)}")
        print()
        print(f"  {C.MAGENTA}╔{'═'*48}╗{C.RESET}")
        print(f"  {C.MAGENTA}║{C.RESET}{C.BOLD}{C.GREEN}{'FIND OFFSET • DONE'.center(48)}{C.RESET}{C.MAGENTA}║{C.RESET}")
        print(f"  {C.MAGENTA}║{C.RESET}  libapp.so: {os.path.basename(lib_path)}")
        print(f"  {C.MAGENTA}║{C.RESET}  success : {success}/{len(false_addresses)}")
        print(f"  {C.MAGENTA}╚{'═'*48}╝{C.RESET}")
        info("libapp.so sudah di-patch di working directory")
        info("Inject manual ke APK atau pakai Flutter Patcher → repack")
    except Exception as e:
        err(f"Patch error: {e}")
        import traceback
        traceback.print_exc()

    input(f"\n{C.YELLOW}Press Enter...{C.RESET}")




# ═══════════════════════════════════════════════════════════════
#  SECTION: SMALI / DEX PATCHER  (MMK MOD)
# ═══════════════════════════════════════════════════════════════

# Smali patterns — exact aktif dari dex_patcher (smngn)
# (pattern yang di-comment di sumber tidak ikut)
MMK_SMALI_PATTERNS = [
    # s1
    (
        re.compile(
            r'(\.method private connectToLicensingService\(\)V\s*\n\s*\.(?:registers|locals) \d+\s*\n)'
        ),
        r'\1    return-void\n',
        "s1",
    ),
    # s2
    (
        re.compile(
            r'(\.method\spublic\sinitializeLicenseCheck\(\)V)(?:\s*\n\s+.*)*?return-void\n\.end\smethod'
        ),
        r'\1\n.registers 1\nreturn-void\n.end method',
        "s2",
    ),
    # s3
    (
        re.compile(
            r'([ias]get-boolean ([pv]\d+)(?!.*(show|display|enablePrepaidPlans)).*;->.*(Premium.*|RemoveAds.*|Pro|ispro|Vip.*|Paid.*|Subscri.*|gold.*|subscri.*|purchase.*|adremoved.*|vip.*|isplus|ProVersion.*|ispaid|purchased|fullversion|unlocked|subscribed|member|adsfree|noads|platinum|enterprise|ultimate|professional):Z)'
        ),
        r'\1\n const/4 \2, 0x1',
        "s3",
    ),
    # s4
    (
        re.compile(
            r'([ias]put-boolean ([pv]\d+)(?!.*(show|display|enablePrepaidPlans)).*;->.*(Premium.*|RemoveAds.*|Pro|ispro|Vip.*|Paid.*|Subscri.*|gold.*|subscri.*|purchase.*|adremoved.*|vip.*|isplus|ProVersion.*|ispaid|purchased|fullversion|unlocked|subscribed|member|adsfree|noads|platinum|enterprise|ultimate|professional):Z)'
        ),
        r'const/4 \2, 0x1\n\n    \1',
        "s4",
    ),
    # s6
    (
        re.compile(
            r'(?i)(const-string[^"]+"(?!(?:.*(?:Disable|Hide|Remove|Free|Basic|Expired|Block)))(?:is|get|has)?(?:Premium.*|Pro\b|Purchased.*|_purchase|NoAds|has_active_p.*|no_ads|Subscriber|Paid\b|vip\b|AdFree|ProVersion|proUser|Elite\b|SUBSCRIBED|AdsRemoved|Upgraded|Subscribed.*|Subscription|lifetime|Unlocked.*)[^"]*"(?:[\s\S]*?)getBoolean\(Ljava/lang/String;Z\)Z[\s\S]{0,50}?)move-result ([pv]\d+)'
        ),
        r'\1\n const/4 \2, 0x1',
        "s6",
    ),
]


def _smali_find_apkeditor():
    found = mmk_find_in_files('apkeditor.jar', 'APKEditor.jar', '*apkeditor*.jar', '*APKEditor*.jar')
    if found:
        return found[0]
    try:
        for f in os.listdir('.'):
            if f.lower().endswith('.jar') and 'apkeditor' in f.lower():
                return os.path.abspath(f)
    except Exception:
        pass
    jars = glob.glob('APKEditor*.jar') + glob.glob('*APKEditor*.jar')
    return os.path.abspath(jars[0]) if jars else None


def _smali_ensure_apkeditor():
    status_search("APKEditor.jar", hold=0.35)
    found = mmk_find_in_files('apkeditor.jar', 'APKEditor.jar', '*apkeditor*.jar', '*APKEditor*.jar')
    if found:
        status_prepare(os.path.basename(found[0]), hold=0.3)
        return found[0]
    jar = _smali_find_apkeditor()
    if jar:
        status_prepare(os.path.basename(str(jar)), hold=0.3)
        return jar
    status_ephemeral("Download APKEditor.jar…", hold=0.4, ok_mark=False)
    mmk_ensure_dirs()
    name = os.path.join(MMK_FILES_DIR, "APKEditor.jar")
    url = "https://github.com/REAndroid/APKEditor/releases/latest/download/APKEditor.jar"
    try:
        spinner("Downloading APKEditor.jar...", 0.8, keep=False)
        req = urllib.request.Request(url, headers={'User-Agent': 'MMK-MOD/1.0'})
        with urllib.request.urlopen(req, timeout=120) as resp, open(name, 'wb') as f:
            shutil.copyfileobj(resp, f)
        status_ephemeral(f"Downloaded {os.path.basename(name)}", hold=0.45)
        return name
    except Exception as e:
        err(f"Download failed: {e}")
        return None


def _smali_patch_file(file_path, patterns):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        return 0, []
    original = content
    hits = []
    for pattern, repl, desc in patterns:
        if repl is None:
            continue
        try:
            new_c, n = pattern.subn(repl, content)
            if n:
                content = new_c
                hits.append(f"{desc}×{n}")
        except Exception:
            pass
    if content != original:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return 1, hits
        except Exception:
            return 0, []
    return 0, []


def _smali_walk_and_patch(decompile_dir):
    banner("SMALI REGEX PATCH", "license · premium · login FB")
    roots = []
    for name in os.listdir(decompile_dir):
        p = os.path.join(decompile_dir, name)
        if os.path.isdir(p) and (name == 'smali' or name.startswith('smali_')):
            roots.append(p)
    if not roots:
        # fallback: any folder with .smali
        for root, dirs, files in os.walk(decompile_dir):
            if any(f.endswith('.smali') for f in files):
                roots.append(root)
                break
    if not roots:
        warn("Folder smali tidak ditemukan")
        return 0

    files = []
    for base in roots:
        for root, _, fs in os.walk(base):
            for fn in fs:
                if fn.endswith('.smali'):
                    fp = os.path.join(root, fn)
                    try:
                        if os.path.getsize(fp) <= 8 * 1024 * 1024:
                            files.append(fp)
                    except OSError:
                        pass

    total = len(files)
    ok(f"{total} file .smali")
    if total == 0:
        return 0

    changed = 0
    for i, fp in enumerate(files, 1):
        c, hits = _smali_patch_file(fp, MMK_SMALI_PATTERNS)
        if c:
            changed += 1
            if changed <= 15 or changed % 25 == 0:
                rel = os.path.relpath(fp, decompile_dir)
                print(f"  {C.GREEN}✓{C.RESET} {rel}  {C.DIM}{', '.join(hits[:3])}{C.RESET}")
        if i % 80 == 0 or i == total:
            progress_bar(i, total, "smali", clear_when_done=(i >= total))
    ok(f"Smali patched: {changed}/{total} files")
    return changed



def _smali_patch_pairip_manifest(decompile_dir):
    """PairIP: hapus CHECK_LICENSE permission + LicenseActivity dari AndroidManifest.xml"""
    banner("PAIRIP MANIFEST", "CHECK_LICENSE + LicenseActivity")
    candidates = [
        os.path.join(decompile_dir, "AndroidManifest.xml"),
        os.path.join(decompile_dir, "AndroidManifest.xml.json"),
    ]
    # also search
    for root, _, files in os.walk(decompile_dir):
        for f in files:
            if f == "AndroidManifest.xml":
                candidates.append(os.path.join(root, f))
    seen = set()
    paths = []
    for p in candidates:
        if p not in seen and os.path.isfile(p):
            seen.add(p)
            paths.append(p)
    if not paths:
        warn("AndroidManifest.xml tidak ditemukan")
        return 0

    total = 0
    for manifest in paths:
        try:
            with open(manifest, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            warn(f"Baca manifest: {e}")
            continue
        original = content

        # hapus uses-permission CHECK_LICENSE
        content, n1 = re.subn(
            r'\s*<uses-permission[^>]*android:name\s*=\s*["\']com\.android\.vending\.CHECK_LICENSE["\'][^>]*/>\s*',
            "\n",
            content,
            flags=re.IGNORECASE,
        )
        # juga format multi-line / tanpa self-close
        content, n1b = re.subn(
            r'\s*<uses-permission[^>]*com\.android\.vending\.CHECK_LICENSE[^>]*/?>\s*',
            "\n",
            content,
            flags=re.IGNORECASE,
        )
        # hapus activity LicenseActivity
        content, n2 = re.subn(
            r'\s*<activity[^>]*android:name\s*=\s*["\']com\.pairip\.licensecheck\.LicenseActivity["\'][\s\S]*?(?:/>|</activity>)\s*',
            "\n",
            content,
            flags=re.IGNORECASE,
        )
        # broader pairip license activity
        content, n2b = re.subn(
            r'\s*<activity[^>]*com\.pairip\.licensecheck\.[^"\']+["\'][\s\S]*?(?:/>|</activity>)\s*',
            "\n",
            content,
            flags=re.IGNORECASE,
        )

        changed = n1 + n1b + n2 + n2b
        if content != original:
            with open(manifest, "w", encoding="utf-8") as f:
                f.write(content)
            ok(f"{os.path.relpath(manifest, decompile_dir)}: {changed} removal(s)")
            if n1 or n1b:
                ok("  − uses-permission CHECK_LICENSE")
            if n2 or n2b:
                ok("  − LicenseActivity")
            total += 1
        else:
            info(f"{os.path.basename(manifest)}: tidak ada entry PairIP")
    return total



def smali_main():
    """Main entry — Smali / DEX patcher (MMK MOD)"""
    banner("SMALI PATCHER", "MMK MOD  •  premium / PairIP / license")
    info("Credit: MMK MOD")
    print()

    if "status_search" in globals():
        try:
            status_search("Java + APKEditor")
            status_prepare("smali patterns")
        except Exception:
            pass

    # ── Session mode: patch saja, build di akhir (Multibypass / Work Session) ──
    if mmk_session_active():
        dec = MMK_SESSION["dec"]
        mmk_session_print_bar()
        banner("SMALI (SESSION)", "patch only · build ditunda")
        changed = _smali_walk_and_patch(dec)
        try:
            _smali_patch_pairip_manifest(dec)
        except Exception as e:
            warn(f"PairIP manifest: {e}")
        mmk_session_log("smali")
        ok(f"Smali patched: {changed} files · ⏸ build ditunda sampai akhir batch")
        return

    if not shutil.which('java'):
        err("Java tidak ditemukan — Termux: pkg install openjdk-17")
        return

    jar = _smali_ensure_apkeditor()
    if not jar:
        err("APKEditor.jar wajib ada di folder ini")
        return

    # select APK / APKS dari app/
    entries = mmk_list_apks()
    if not entries:
        err(f"Tidak ada file APK/APKS di {MMK_APP_DIR}")
        return

    if 'select_target' in globals():
        chosen = select_target(entries, title="SELECT TARGET  •  SMALI APK")
        if not chosen:
            info("Dibatalkan")
            return
        apk_path = chosen
    else:
        apk_path = entries[0][0]

    ok(f"Target: {os.path.basename(apk_path)}")
    work_root = os.getcwd()
    jar_abs = os.path.join(work_root, jar) if not os.path.isabs(jar) else jar

    # merge APKS if needed
    if apk_path.lower().endswith(('.apks', '.xapk')):
        banner("MERGE APKS", os.path.basename(apk_path))
        out_merge = os.path.splitext(apk_path)[0] + '_merged.apk'
        spinner("Merging split APK...", 1.0)
        rc = run_java_quiet(['java', '-jar', jar_abs, 'm', '-i', apk_path, '-o', out_merge, '-f'], label="MERGE")
        if rc != 0 or not os.path.exists(out_merge):
            err("Merge APKS gagal")
            return
        apk_path = out_merge
        ok(f"Merged: {os.path.basename(apk_path)}")

    base = os.path.splitext(os.path.basename(apk_path))[0]
    decompile_dir = os.path.join(work_root, f"{base}_smali_dec")
    output_apk = mmk_output("patched", f"{base}-smali-patched.apk")

    if os.path.isdir(decompile_dir):
        spinner("Hapus decompile lama...", 0.5)
        shutil.rmtree(decompile_dir, ignore_errors=True)

    banner("DECOMPILE", "APKEditor d -i apk -o folder")
    box_cmd_short("decompile", apk_path, decompile_dir, "smali")
    rc = run_java_quiet(
        ['java', '-jar', jar_abs, 'd', '-i', apk_path, '-o', decompile_dir, '-f'],
        label="DECOMPILE",
    )
    if rc != 0 or not os.path.isdir(decompile_dir):
        err("Decompile gagal")
        return
    ok(f"Decompiled → {os.path.basename(decompile_dir)}")

    changed = _smali_walk_and_patch(decompile_dir)

    # PairIP manifest cleanup
    try:
        _smali_patch_pairip_manifest(decompile_dir)
    except Exception as e:
        warn(f"PairIP manifest: {e}")

    banner("BUILD APK", "APKEditor b")
    spinner("Building patched APK...", 1.5)
    if os.path.exists(output_apk):
        try:
            os.remove(output_apk)
        except Exception:
            pass
    rc = subprocess.call(
        ['java', '-jar', jar_abs, 'b', '-i', decompile_dir, '-o', output_apk]
    )
    if rc != 0 or not os.path.exists(output_apk):
        err("Build gagal")
        return

    size = human_size(os.path.getsize(output_apk))
    out_dir = os.path.dirname(os.path.abspath(output_apk))
    print()
    print(f"  {C.MAGENTA}╔{'═'*58}╗{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}{C.BOLD}{C.GREEN}{'SMALI PATCH COMPLETE — MMK MOD'.center(58)}{C.RESET}{C.MAGENTA}║{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  Output    : {C.CYAN}{os.path.basename(output_apk)}{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  Size      : {size}")
    print(f"  {C.MAGENTA}║{C.RESET}  Files     : {changed} smali changed")
    print(f"  {C.MAGENTA}║{C.RESET}  Direktori : {C.CYAN}{out_dir[:44]}{C.RESET}")
    if len(out_dir) > 44:
        print(f"  {C.MAGENTA}║{C.RESET}              {C.DIM}{out_dir[44:88]}{C.RESET}")
    print(f"  {C.MAGENTA}╚{'═'*58}╝{C.RESET}")
    print()

    # optional cleanup decompile
    ans = input(f"  {C.YELLOW}Hapus folder decompile? [y/N]{C.RESET} ➤ ").strip().lower()
    if ans in ('y', 'ya', 'yes', '1'):
        shutil.rmtree(decompile_dir, ignore_errors=True)
        ok("Decompile folder dihapus")




# ─── Sign APK + Inject DEX/Hook (Toolkit 9 & 10) — MMK MOD ─────

def _list_files_ext(ext):
    """Return list of absolute paths for extension, prefer app/ folder."""
    if isinstance(ext, str):
        exts = (ext,)
    else:
        exts = tuple(ext)
    if any(e.lower() in (".apk", ".apks", ".xapk", ".aab") for e in exts):
        return [e[0] for e in mmk_list_apks(exts)]
    out = []
    for d in (MMK_APP_DIR, os.getcwd(), MMK_FILES_DIR):
        if not d or not os.path.isdir(d):
            continue
        try:
            for f in sorted(os.listdir(d)):
                if any(f.lower().endswith(e.lower()) for e in exts):
                    fp = os.path.join(d, f)
                    if os.path.isfile(fp):
                        out.append(os.path.abspath(fp))
        except OSError:
            pass
    return out


def _pick_from_entries(entries, title):
    if not entries:
        return None
    if "select_target" in globals():
        return select_target(entries, title=title)
    for i, (_, name, sz) in enumerate(entries, 1):
        print(f"  {C.GREEN}{i:2d}{C.RESET}  {name:<42} {C.CYAN}{human_size(sz):>10}{C.RESET}")
    print(f"  {C.RED} 0{C.RESET}  BACK")
    try:
        raw = input(f"\n{C.MAGENTA}𝙿𝚒𝚕𝚒𝚑 𝚗𝚘𝚖𝚘𝚛 ➤{C.RESET} ").strip()
        if raw == "0":
            return None
        return entries[int(raw) - 1][0]
    except Exception:
        return None


def _next_classes_dex_name(apk_path):
    """Jika ada classes5.dex → return classes6.dex; jika hanya classes.dex → classes2.dex"""
    nums = set()
    with zipfile.ZipFile(apk_path, "r") as z:
        for n in z.namelist():
            base = os.path.basename(n)
            if base == "classes.dex":
                nums.add(1)
            else:
                m = re.match(r"^classes(\d+)\.dex$", base, re.I)
                if m:
                    nums.add(int(m.group(1)))
    if not nums:
        return "classes.dex"
    nxt = max(nums) + 1
    if nxt == 1:
        return "classes.dex"
    return f"classes{nxt}.dex"


def run_sign_apk_interactive():
    """Sign APK dengan .jks / .keystore di direktori (jarsigner / apksigner)."""
    banner("SIGN APK", "MMK MOD  •  .jks / .keystore")
    info("Mencari keystore di folder kerja...")

    keys = _list_files_ext(".jks", ".keystore", ".key")
    # .key sering bukan java keystore — tetap tampilkan jks/keystore dulu
    keys = [e for e in keys if e[1].lower().endswith((".jks", ".keystore"))] + \
           [e for e in keys if e[1].lower().endswith(".key")]
    if not keys:
        warn("Tidak ada .jks/.keystore — buat debug.jks otomatis?")
        ans = input(f"  {C.CYAN}Buat debug.jks? [Y/n]{C.RESET} ➤ ").strip().lower()
        if ans in ("n", "no", "tidak"):
            info("Sesi dihentikan")
            input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
            return
        if not shutil.which("keytool"):
            err("keytool tidak ada (pkg install openjdk-17)")
            input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
            return
        key_path = os.path.abspath("debug.jks")
        spinner("keytool -genkeypair debug.jks...", 1.0)
        rc = subprocess.call([
            "keytool", "-genkeypair", "-v",
            "-keystore", key_path,
            "-alias", "androiddebugkey",
            "-keyalg", "RSA", "-keysize", "2048",
            "-validity", "10000",
            "-storepass", "android",
            "-keypass", "android",
            "-dname", "CN=MMK MOD, OU=MMK, O=MMK MOD, L=ID, ST=ID, C=ID",
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if rc != 0 or not os.path.exists(key_path):
            err("Gagal buat debug.jks")
            input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
            return
        ok("debug.jks dibuat (alias=androiddebugkey, pass=android)")
        keys = [(key_path, "debug.jks", os.path.getsize(key_path))]

    key_path = _pick_from_entries(keys, "SELECT KEYSTORE  •  .jks/.keystore")
    if not key_path:
        info("Dibatalkan")
        return
    ok(f"Keystore: {os.path.basename(key_path)}")

    entries = mmk_list_apks((".apk",))
    if not entries:
        err(f"Tidak ada APK untuk di-sign di {MMK_APP_DIR}")
        input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
        return
    apk_path = _pick_from_entries(entries, "SELECT APK  •  TO SIGN")
    if not apk_path:
        info("Dibatalkan")
        return
    ok(f"APK: {os.path.basename(apk_path)}")

    print()
    alias = input(f"  {C.CYAN}Key alias{C.RESET} [{C.DIM}key0{C.RESET}] ➤ ").strip() or "key0"
    storepass = input(f"  {C.CYAN}Store password{C.RESET} [{C.DIM}android{C.RESET}] ➤ ").strip() or "android"
    keypass = input(f"  {C.CYAN}Key password{C.RESET} [{C.DIM}sama store{C.RESET}] ➤ ").strip() or storepass

    stem = Path(apk_path).stem
    out_apk = f"{stem}-signed.apk"
    print()
    out_custom = input(f"  {C.CYAN}Output{C.RESET} [{C.DIM}{out_apk}{C.RESET}] ➤ ").strip()
    if out_custom:
        out_apk = out_custom if out_custom.endswith(".apk") else out_custom + ".apk"

    # zipalign optional
    aligned = f"{stem}-aligned.apk"
    zipalign = shutil.which("zipalign")
    if zipalign:
        spinner("zipalign...", 0.8)
        subprocess.call([zipalign, "-f", "-p", "4", apk_path, aligned],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(aligned):
            sign_input = aligned
            ok("zipalign OK")
        else:
            sign_input = apk_path
            warn("zipalign gagal — pakai APK asli")
    else:
        sign_input = apk_path
        info("zipalign tidak ada — skip")

    apksigner = shutil.which("apksigner")
    jarsigner = shutil.which("jarsigner")

    banner("SIGNING", os.path.basename(out_apk))
    ok_sign = False

    if apksigner:
        spinner("apksigner sign...", 1.2)
        cmd = [
            apksigner, "sign",
            "--ks", key_path,
            "--ks-key-alias", alias,
            "--ks-pass", f"pass:{storepass}",
            "--key-pass", f"pass:{keypass}",
            "--out", out_apk,
            sign_input,
        ]
        rc = subprocess.call(cmd)
        ok_sign = rc == 0 and os.path.exists(out_apk)
    elif jarsigner:
        spinner("jarsigner...", 1.2)
        # jarsigner signs in-place → copy first
        shutil.copy2(sign_input, out_apk)
        cmd = [
            jarsigner,
            "-keystore", key_path,
            "-storepass", storepass,
            "-keypass", keypass,
            "-sigalg", "SHA256withRSA",
            "-digestalg", "SHA-256",
            out_apk,
            alias,
        ]
        rc = subprocess.call(cmd)
        ok_sign = rc == 0 and os.path.exists(out_apk)
    else:
        err("apksigner / jarsigner tidak ditemukan")
        info("Termux: pkg install android-tools  atau  openjdk (jarsigner)")
        input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
        return

    # cleanup aligned temp
    if os.path.exists(aligned) and aligned != out_apk:
        try:
            os.remove(aligned)
        except Exception:
            pass

    if ok_sign:
        print()
        print(f"  {C.MAGENTA}╔{'═'*48}╗{C.RESET}")
        print(f"  {C.MAGENTA}║{C.RESET}{C.BOLD}{C.GREEN}{'SIGNED — MMK MOD'.center(48)}{C.RESET}{C.MAGENTA}║{C.RESET}")
        print(f"  {C.MAGENTA}║{C.RESET}  Output: {C.CYAN}{out_apk}{C.RESET}")
        print(f"  {C.MAGENTA}║{C.RESET}  Size  : {human_size(os.path.getsize(out_apk))}")
        print(f"  {C.MAGENTA}╚{'═'*48}╝{C.RESET}")
    else:
        err("Sign gagal — cek alias / password keystore")
    input(f"\n{C.YELLOW}Press Enter...{C.RESET}")


def _inject_dex_into_apk(apk_path, dex_path, entry_name):
    """Tambah file dex ke APK sebagai entry_name (mis. classes6.dex)."""
    out_apk = f"{Path(apk_path).stem}-dexinjected.apk"
    tmp = out_apk + ".tmp"
    with zipfile.ZipFile(apk_path, "r") as zin, zipfile.ZipFile(tmp, "w") as zout:
        for item in zin.infolist():
            # skip if same name already
            if item.filename == entry_name or item.filename.endswith("/" + entry_name):
                continue
            zout.writestr(item, zin.read(item.filename))
        # write new dex
        with open(dex_path, "rb") as f:
            data = f.read()
        info = zipfile.ZipInfo(entry_name)
        info.compress_type = zipfile.ZIP_DEFLATED
        zout.writestr(info, data)
    os.replace(tmp, out_apk)
    return out_apk


def _inject_hook_into_smali(decompile_dir, hook_line, activity=None):
    """
    Cari method onCreate / onResume di smali (opsional filter Activity),
    sisipkan hook setelah header method.
    activity: com.example.MainActivity atau path smali
    """
    hook_line = hook_line.strip()
    if not hook_line.startswith(" "):
        hook_insn = "    " + hook_line
    else:
        hook_insn = hook_line

    method_re = re.compile(
        r'(\.method\s+[^\n]*(onCreate|onResume)\([^\)]*\)V\s*\n'
        r'(?:\s*\.(?:registers|locals)\s+\d+\s*\n)?'
        r'(?:\s*\.param[^\n]*\n)*)',
        re.IGNORECASE,
    )

    # target file filter
    target_suffix = None
    if activity:
        act = activity.strip().replace(".", "/")
        if act.startswith("L") and act.endswith(";"):
            act = act[1:-1]
        if not act.endswith(".smali"):
            act += ".smali"
        target_suffix = act

    changed = 0
    smali_roots = []
    for name in os.listdir(decompile_dir):
        p = os.path.join(decompile_dir, name)
        if os.path.isdir(p) and (name == "smali" or name.startswith("smali_")):
            smali_roots.append(p)
    if not smali_roots:
        smali_roots = [decompile_dir]

    files_hit = []
    for base in smali_roots:
        for root, _, files in os.walk(base):
            for fn in files:
                if not fn.endswith(".smali"):
                    continue
                fp = os.path.join(root, fn)
                if target_suffix:
                    norm = fp.replace("\\", "/")
                    if not (norm.endswith(target_suffix) or fn == os.path.basename(target_suffix)):
                        continue
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except Exception:
                    continue
                if "onCreate" not in content and "onResume" not in content:
                    continue

                def _inject(m, _hook=hook_insn):
                    block = m.group(0)
                    if "Zxdialogs" in block or _hook.strip() in block:
                        return block
                    return block + _hook + "\n"

                new_c, n = method_re.subn(_inject, content)
                if n and new_c != content:
                    try:
                        with open(fp, "w", encoding="utf-8") as f:
                            f.write(new_c)
                        changed += n
                        files_hit.append(os.path.relpath(fp, decompile_dir))
                    except Exception:
                        pass
    return changed, files_hit


def run_inject_dex_hook_interactive():
    """
    1) Pilih APK
    2) Pilih .dex → inject sebagai classes(N+1).dex
    3) Opsional: inject hook invoke-static ke onCreate/onResume
    """
    banner("INJECT DEX + HOOK", "MMK MOD  •  classesN.dex + onCreate")

    entries = mmk_list_apks((".apk",))
    if not entries:
        err(f"Tidak ada APK di {MMK_APP_DIR}")
        input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
        return
    apk_path = _pick_from_entries(entries, "SELECT APK  •  TARGET")
    if not apk_path:
        return
    ok(f"APK: {os.path.basename(apk_path)}")

    dexes = _list_files_ext(".dex")
    if not dexes:
        err("Tidak ada file .dex di folder")
        info("Letakkan classes.dex / hook.dex di direktori ini")
        input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
        return
    dex_path = _pick_from_entries(dexes, "SELECT DEX  •  TO INJECT")
    if not dex_path:
        return
    ok(f"DEX: {os.path.basename(dex_path)}")

    next_name = _next_classes_dex_name(apk_path)
    info(f"Akan disisipkan sebagai: {C.CYAN}{next_name}{C.RESET}")

    print()
    print(f"  {C.BOLD}{C.CYAN}▶ ACTIVITY{C.RESET}")
    print(f"  {C.DIM}Contoh: com.example.MainActivity{C.RESET}")
    activity = input(f"  {C.CYAN}Activity{C.RESET} ➤ ").strip()

    print()
    print(f"  {C.BOLD}{C.CYAN}▶ HOOK CODE{C.RESET}")
    print(f"  {C.DIM}Contoh:{C.RESET}")
    print(f"  {C.DIM}invoke-static {{p0}}, Lcom/zx/zendialogs/Zxdialogs;->show(Landroid/content/Context;)V{C.RESET}")
    default_hook = "invoke-static {p0}, Lcom/zx/zendialogs/Zxdialogs;->show(Landroid/content/Context;)V"
    hook = input(f"\n  {C.CYAN}Hook line{C.RESET} [{C.DIM}Enter = default{C.RESET}] ➤ ").strip()
    if not hook:
        hook = default_hook
        ok(f"Hook default: {hook[:60]}...")

    banner("INJECT DEX", f"{os.path.basename(dex_path)} → {next_name}")
    spinner("Menulis APK...", 1.0)
    try:
        out_apk = _inject_dex_into_apk(apk_path, dex_path, next_name)
        ok(f"DEX injected → {os.path.basename(out_apk)}")
    except Exception as e:
        err(f"Inject DEX gagal: {e}")
        input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
        return

    if hook:
        jar = None
        for finder in ("_smali_ensure_apkeditor", "_smali_find_apkeditor", "find_apkeditor_jar"):
            if finder in globals():
                try:
                    jar = globals()[finder]()
                except Exception:
                    jar = None
                if jar:
                    break
        if not jar:
            # last try listdir
            for f in os.listdir("."):
                if f.lower().endswith(".jar") and "apkeditor" in f.lower():
                    jar = f
                    break
        if not jar:
            warn("APKEditor tidak ada — hook smali di-skip (DEX tetap ter-inject)")
        elif not shutil.which("java"):
            warn("Java tidak ada — hook smali di-skip")
        else:
            banner("INJECT HOOK", "onCreate / onResume")
            work = f"{Path(out_apk).stem}_hook_dec"
            if os.path.isdir(work):
                shutil.rmtree(work, ignore_errors=True)
            spinner("Decompile untuk sisip hook...", 1.5)
            rc = run_java_quiet(["java", "-jar", jar, "d", "-i", out_apk, "-o", work], label="DECOMPILE")
            if rc != 0 or not os.path.isdir(work):
                err("Decompile gagal — DEX sudah di APK, hook batal")
            else:
                n, hits = _inject_hook_into_smali(work, hook, activity=activity if activity else None)
                ok(f"Hook disisipkan di {n} method(s)")
                for h in hits[:12]:
                    print(f"  {C.GREEN}◆{C.RESET} {h}")
                if len(hits) > 12:
                    info(f"... +{len(hits)-12} file lain")
                final_out = f"{Path(apk_path).stem}-injected.apk"
                spinner("Rebuild APK...", 1.5)
                if os.path.exists(final_out):
                    try:
                        os.remove(final_out)
                    except Exception:
                        pass
                rc = run_java_quiet(["java", "-jar", jar, "b", "-i", work, "-o", final_out], label="BUILD")
                if rc == 0 and os.path.exists(final_out):
                    # replace intermediate
                    try:
                        if out_apk != final_out and os.path.exists(out_apk):
                            os.remove(out_apk)
                    except Exception:
                        pass
                    out_apk = final_out
                    ok(f"Rebuild OK → {os.path.basename(out_apk)}")
                else:
                    err("Rebuild gagal — pakai APK hasil inject DEX saja")
                # cleanup
                ans = input(f"  {C.YELLOW}Hapus folder decompile? [Y/n]{C.RESET} ➤ ").strip().lower()
                if ans not in ("n", "no", "tidak"):
                    shutil.rmtree(work, ignore_errors=True)

    print()
    print(f"  {C.MAGENTA}╔{'═'*50}╗{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}{C.BOLD}{C.GREEN}{'INJECT DONE — MMK MOD'.center(50)}{C.RESET}{C.MAGENTA}║{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  Output : {C.CYAN}{os.path.basename(out_apk)}{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  DEX as : {next_name}")
    print(f"  {C.MAGENTA}║{C.RESET}  Hook   : {'yes' if hook else 'no'}")
    print(f"  {C.MAGENTA}║{C.RESET}  Size   : {human_size(os.path.getsize(out_apk))}")
    print(f"  {C.MAGENTA}╚{'═'*50}╝{C.RESET}")
    info("Sign APK setelah inject (Toolkit → 9 Sign APK)")
    input(f"\n{C.YELLOW}Press Enter...{C.RESET}")



def toolkit_main():
    """Launch Nexus Cloud Toolkit (option 4)"""
    try:
        # ensure rich
        try:
            from rich.console import Console
        except ImportError:
            print("  Installing rich + requests...")
            os.system(f"{sys.executable} -m pip install rich requests -q")
        app = NexusCloudTerminal()
        app.nexus_main_menu()
    except KeyboardInterrupt:
        print("\n  Toolkit closed")
    except Exception as e:
        print(f"  Toolkit error: {e}")
        import traceback
        traceback.print_exc()


# ═══════════════════════════════════════════════════════════════
#  ENTRY
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
#  SECTION: SIGN APK + INJECT DIALOG  (MMK MOD)
# ═══════════════════════════════════════════════════════════════

def _pick_files_by_ext(exts, title):
    files = []
    for f in sorted(os.listdir('.')):
        low = f.lower()
        if any(low.endswith(e) for e in exts) and os.path.isfile(f):
            try:
                sz = os.path.getsize(f)
            except OSError:
                sz = 0
            files.append((os.path.abspath(f), f, sz))
    if not files:
        err(f"Tidak ada file {exts} di folder ini")
        return None
    if 'select_target' in globals():
        return select_target(files, title=title)
    for i, (_, name, sz) in enumerate(files, 1):
        print(f"  {C.GREEN}{i:2d}{C.RESET}  {name}  {C.CYAN}{human_size(sz)}{C.RESET}")
    try:
        idx = int(input(f"  {C.MAGENTA}➤{C.RESET} ").strip())
        return files[idx - 1][0]
    except Exception:
        return None


def _list_keystore_files():
    keys = []
    for f in sorted(os.listdir('.')):
        low = f.lower()
        if low.endswith(('.jks', '.keystore', '.key')) and os.path.isfile(f):
            keys.append(f)
    return keys


def _auto_keystore_creds(keystore):
    """
    Deteksi password + alias otomatis — tanpa input user.
    Coba pass umum + env MMK_KS_PASS / MMK_KEY_PASS.
    Return (storepass, keypass, alias) atau (None, None, None).
    """
    candidates = []
    env_sp = os.environ.get("MMK_KS_PASS", "").strip()
    env_kp = os.environ.get("MMK_KEY_PASS", "").strip()
    if env_sp:
        candidates.append(env_sp)
    candidates.extend([
        "android", "Android", "password", "Password", "123456",
        "changeit", "secret", "keystore", "mmk", "mod", "",
    ])
    # unique keep order
    seen = set()
    passes = []
    for p in candidates:
        if p not in seen:
            seen.add(p)
            passes.append(p)

    if not shutil.which("keytool"):
        # fallback defaults
        return (env_sp or "android", env_kp or env_sp or "android", "androiddebugkey")

    for sp in passes:
        try:
            cmd = ["keytool", "-list", "-keystore", keystore, "-storepass", sp]
            out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, timeout=25)
        except Exception:
            continue
        alias = None
        for line in out.splitlines():
            if "PrivateKeyEntry" in line or "SecretKeyEntry" in line:
                alias = line.split(",")[0].strip()
                break
        if not alias:
            # baris alias kadang "alias_name, ..."
            for line in out.splitlines():
                line = line.strip()
                if line and not line.startswith(("Keystore", "Your", "Warning", "*")) and "," in line:
                    alias = line.split(",")[0].strip()
                    break
        if not alias:
            alias = "androiddebugkey"
        kp = env_kp or sp
        return (sp, kp, alias)
    return (None, None, None)


def sign_apk_main():
    """
    Sign APK — pilih .apk + .jks/.key saja.
    Tidak perlu input password/alias (auto-detect).
    """
    banner("SIGN APK", "MMK MOD  •  auto .jks/.key  •  tanpa input sandi")
    info("Credit: MMK MOD")
    info("Cukup pilih APK + keystore — password/alias dideteksi otomatis")
    print()

    apk = _pick_files_by_ext(('.apk',), "SELECT APK  •  SIGN")
    if not apk:
        return
    ok(f"APK: {os.path.basename(apk)}")

    keys = _list_keystore_files()
    if not keys:
        err("Tidak ada .jks / .keystore / .key di folder ini")
        info("Letakkan file keystore di direktori kerja")
        return

    entries = [(os.path.abspath(k), k, os.path.getsize(k)) for k in keys]
    if 'select_target' in globals():
        keystore = select_target(entries, title="SELECT KEYSTORE  •  .jks / .key")
        if not keystore:
            return
    else:
        keystore = os.path.abspath(keys[0])
    ok(f"Keystore: {os.path.basename(keystore)}")

    spinner("Auto-detect password & alias...", 0.8)
    storepass, keypass, alias = _auto_keystore_creds(keystore)
    if not storepass:
        err("Gagal buka keystore — password tidak dikenali")
        info("Set env: export MMK_KS_PASS='sandi_keystore'")
        return
    ok(f"Alias: {alias}")
    ok("Password: (auto)")

    out_apk = os.path.splitext(apk)[0] + "-signed.apk"
    shutil.copy2(apk, out_apk)

    banner("SIGNING", os.path.basename(out_apk))
    signed = False

    apksigner = shutil.which('apksigner')
    if apksigner:
        spinner("apksigner sign...", 1.0)
        cmd = [
            apksigner, 'sign',
            '--ks', keystore,
            '--ks-pass', f'pass:{storepass}',
            '--key-pass', f'pass:{keypass}',
            '--ks-key-alias', alias,
            out_apk,
        ]
        rc = subprocess.call(cmd)
        if rc == 0:
            ok("Signed with apksigner")
            signed = True
        else:
            warn("apksigner gagal — coba jarsigner")

    if not signed and shutil.which('jarsigner'):
        spinner("jarsigner...", 1.0)
        cmd = [
            'jarsigner', '-sigalg', 'SHA256withRSA', '-digestalg', 'SHA-256',
            '-keystore', keystore,
            '-storepass', storepass,
            '-keypass', keypass,
            out_apk, alias,
        ]
        rc = subprocess.call(cmd)
        if rc == 0:
            ok("Signed with jarsigner")
            signed = True
            if shutil.which('zipalign'):
                aligned = out_apk + ".aligned"
                subprocess.call(['zipalign', '-f', '4', out_apk, aligned])
                if os.path.exists(aligned):
                    os.replace(aligned, out_apk)
                    ok("zipalign OK")

    if not signed:
        err("Sign gagal — cek keystore / set MMK_KS_PASS")
        try:
            os.remove(out_apk)
        except Exception:
            pass
        return

    print()
    print(f"  {C.MAGENTA}╔{'═'*48}╗{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}{C.BOLD}{C.GREEN}{'SIGN COMPLETE — MMK MOD'.center(48)}{C.RESET}{C.MAGENTA}║{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  Output: {C.CYAN}{os.path.basename(out_apk)}{C.RESET}")
    print(f"  {C.MAGENTA}╚{'═'*48}╝{C.RESET}")


def _apkeditor_supports_protect(jar_abs):
    """Cek apakah jar punya command p|protect (via p -h)."""
    try:
        r = subprocess.run(
            ["java", "-jar", jar_abs, "p", "-h"],
            capture_output=True, text=True, timeout=60,
        )
        out = (r.stdout or "") + (r.stderr or "")
        low = out.lower()
        return ("protect" in low) or ("-i" in low and "input" in low) or r.returncode == 0
    except Exception:
        return False


def _download_apkeditor_latest(dest_dir="."):
    """
    Unduh APKEditor.jar terbaru dari GitHub REAndroid/APKEditor.
    Return path absolut jar atau None.
    """
    dest_dir = os.path.abspath(dest_dir)
    os.makedirs(dest_dir, exist_ok=True)
    # URL release terbaru (fallback hardcode V1.4.9)
    urls = [
        "https://github.com/REAndroid/APKEditor/releases/download/V1.4.9/APKEditor-1.4.9.jar",
        "https://github.com/REAndroid/APKEditor/releases/latest/download/APKEditor.jar",
    ]
    try:
        import urllib.request
        import json as _json
        req = urllib.request.Request(
            "https://api.github.com/repos/REAndroid/APKEditor/releases/latest",
            headers={"User-Agent": "MMK-MOD"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = _json.loads(resp.read().decode())
        for a in data.get("assets") or []:
            name = a.get("name") or ""
            if name.lower().endswith(".jar") and "apkeditor" in name.lower():
                urls.insert(0, a["browser_download_url"])
                break
    except Exception as e:
        warn(f"API GitHub: {e} — pakai URL fallback")

    out_jar = os.path.join(dest_dir, "APKEditor.jar")
    for url in urls:
        try:
            info(f"Download: {url}")
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": "MMK-MOD"})
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = resp.read()
            if len(data) < 100_000:
                warn(f"File terlalu kecil ({len(data)} B) — skip")
                continue
            with open(out_jar, "wb") as f:
                f.write(data)
            # juga simpan nama versi
            ver_name = url.rstrip("/").split("/")[-1]
            if ver_name.lower().endswith(".jar") and ver_name != "APKEditor.jar":
                alt = os.path.join(dest_dir, ver_name)
                try:
                    shutil.copy2(out_jar, alt)
                except Exception:
                    pass
            ok(f"Saved: {out_jar} ({human_size(len(data))})")
            return out_jar
        except Exception as e:
            warn(f"Gagal unduh: {e}")
    return None


def _find_or_fetch_apkeditor():
    """Cari jar lokal; jika tidak support protect → unduh terbaru."""
    candidates = []
    try:
        j = _smali_ensure_apkeditor()
        if j:
            candidates.append(os.path.abspath(j))
    except Exception:
        pass
    for f in sorted(os.listdir(".")):
        low = f.lower()
        if low.endswith(".jar") and "apkeditor" in low:
            candidates.append(os.path.abspath(f))
    # dedupe
    seen = set()
    jars = []
    for c in candidates:
        if c not in seen and os.path.isfile(c):
            seen.add(c)
            jars.append(c)

    for jar in jars:
        ok(f"Cek protect support: {os.path.basename(jar)}")
        if _apkeditor_supports_protect(jar):
            ok(f"OK — support command p: {os.path.basename(jar)}")
            return jar
        warn(f"{os.path.basename(jar)} tidak support 'p' / protect")

    banner("DOWNLOAD", "APKEditor terbaru dari GitHub")
    info("https://github.com/REAndroid/APKEditor/releases")
    jar = _download_apkeditor_latest(".")
    if jar and _apkeditor_supports_protect(jar):
        return jar
    if jar:
        warn("Jar terunduh tapi p -h gagal — tetap dicoba")
        return jar
    return jars[0] if jars else None


def _find_dpt_jar():
    """Cari dpt.jar (dpt-shell) di folder kerja / tools."""
    names = ("dpt.jar", "dpt-shell.jar")
    dirs = [".", "tools", "dpt", "dpt-shell", str(Path.home() / "dpt-shell")]
    for d in dirs:
        if not os.path.isdir(d) and d not in (".",):
            continue
        base = d if os.path.isdir(d) else "."
        for root, _, files in os.walk(base):
            for f in files:
                if f.lower() in names or (f.lower().startswith("dpt") and f.lower().endswith(".jar")):
                    return os.path.abspath(os.path.join(root, f))
            # jangan terlalu dalam
            if root.count(os.sep) - base.count(os.sep) > 3:
                break
    return None


def _download_dpt_shell(dest_dir="."):
    """Unduh dpt-shell release dari GitHub (DEX shell high-level)."""
    import urllib.request
    dest_dir = os.path.abspath(dest_dir)
    os.makedirs(dest_dir, exist_ok=True)
    api = "https://api.github.com/repos/luoyesiqiu/dpt-shell/releases/latest"
    try:
        req = urllib.request.Request(api, headers={"User-Agent": "MMK-MOD"})
        with urllib.request.urlopen(req, timeout=60) as r:
            meta = json.loads(r.read().decode())
    except Exception as e:
        warn(f"API dpt-shell: {e}")
        return None
    assets = meta.get("assets") or []
    url = None
    for a in assets:
        name = a.get("name") or ""
        if name.endswith(".zip") or name.endswith(".jar"):
            url = a.get("browser_download_url")
            if name.endswith(".jar"):
                break
    if not url:
        # fallback known release
        url = "https://github.com/luoyesiqiu/dpt-shell/releases/download/v2.21.0/dpt-shell-v2.21.0.zip"
    info(f"Download: {url}")
    zip_path = os.path.join(dest_dir, "dpt-shell-dl.zip")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MMK-MOD"})
        with urllib.request.urlopen(req, timeout=300) as r:
            data = r.read()
        open(zip_path, "wb").write(data)
    except Exception as e:
        err(f"Download dpt gagal: {e}")
        return None
    # extract
    out_dir = os.path.join(dest_dir, "dpt-shell")
    try:
        if zip_path.endswith(".jar"):
            jar = os.path.join(dest_dir, "dpt.jar")
            shutil.copy2(zip_path, jar)
            return jar
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(out_dir)
    except Exception as e:
        err(f"Extract dpt: {e}")
        return None
    for root, _, files in os.walk(out_dir):
        for f in files:
            if f.endswith(".jar") and "dpt" in f.lower():
                return os.path.abspath(os.path.join(root, f))
    # kadang jar bernama executable/dpt.jar
    for root, _, files in os.walk(out_dir):
        for f in files:
            if f.endswith(".jar"):
                return os.path.abspath(os.path.join(root, f))
    return None


def _smali_high_obfuscate_file(path):
    """
    Obfuscate 1 file smali — AMAN (tidak merusak struktur method).

    Penyebab error sebelumnya:
      - menghapus `.param` → sisa `.annotation` / `.end param` yatim
      - inject `goto` langsung setelah `.registers` (sebelum annotation/param)
      → SmaliParseException: expecting '.end method'

    Aturan aman:
      1) JANGAN hapus .param / .annotation / .end annotation / .end param
      2) Hanya strip .line / .local (debug)
      3) Inject opaque-predicate HANYA setelah semua directive method
         (setelah .prologue ATAU di instruksi bytecode pertama)
      4) Skip method abstract/native
      5) Skip package framework (androidx, google, kotlin, ...)
    """
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            src = f.read()
    except Exception:
        return False

    # skip library / framework — jangan sentuh
    # path biasanya .../smali/classes/com/android/... atau L-type di .class
    low_path = path.replace("\\", "/").lower()
    skip_pkgs = (
        "/android/", "/androidx/", "/kotlin/", "/kotlinx/",
        "/dalvik/", "/java/", "/javax/",
        "/com/google/", "/com/android/billingclient/",
        "/com/android/vending/", "/okhttp3/", "/okio/",
        "/retrofit2/", "/com/squareup/",
    )
    if any(p in low_path for p in skip_pkgs):
        return False
    head = src[:1200]
    if any(x in head for x in (
        ".class public final Landroid/",
        ".class public Landroid/",
        ".class Landroidx/",
        ".class Lkotlin/",
        ".class Lcom/google/",
        ".class Lcom/android/billingclient/",
    )):
        return False

    lines = src.splitlines(keepends=True)
    out = []
    changed = False
    import random
    rnd = random.Random(hash(path) & 0xFFFFFFFF)

    # state per method
    in_method = False
    method_is_stub = False  # abstract/native
    directives_done = False  # sudah lewat .registers/.param/.annotation/.prologue
    junk_injected = False

    DIRECTIVE_PREFIXES = (
        ".registers ", ".locals ",
        ".param ", ".end param",
        ".annotation ", ".end annotation",
        ".prologue", ".catch ", ".catchall ",
        ".array-data", ".end array-data",
        ".packed-switch", ".end packed-switch",
        ".sparse-switch", ".end sparse-switch",
        ".line ", ".local ", ".end local",
        ".restart local",
    )

    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()

        # ── method boundary ──
        if s.startswith(".method "):
            in_method = True
            method_is_stub = (" abstract " in f" {s} ") or s.endswith(" abstract") or (
                " native " in f" {s} "
            ) or s.endswith(" native")
            directives_done = False
            junk_injected = False
            out.append(line)
            i += 1
            continue
        if s.startswith(".end method"):
            in_method = False
            method_is_stub = False
            directives_done = False
            junk_injected = False
            out.append(line)
            i += 1
            continue

        if not in_method or method_is_stub:
            out.append(line)
            i += 1
            continue

        # ── strip debug SAJA (jangan .param!) ──
        if s.startswith(".line ") or s.startswith(".local ") or s.startswith(".end local") or s.startswith(".restart local"):
            changed = True
            i += 1
            continue

        # ── masih di zona directive? ──
        is_directive = (
            s.startswith(".") and not s.startswith(".end method")
        ) or s.startswith("#") or s == ""
        # instruksi nyata: tidak mulai dengan . atau : (label) di zona awal
        # label (:xxx) masih boleh sebelum junk? setelah prologue ok
        if not directives_done:
            if s.startswith(".prologue"):
                out.append(line)
                directives_done = True
                # inject SEGERA setelah prologue
                if not junk_injected:
                    n = rnd.randint(10000, 99999)
                    out.append(f"    goto :mmk_ok_{n}\n")
                    out.append(f"    :mmk_dead_{n}\n")
                    out.append(f"    nop\n")
                    out.append(f"    goto :mmk_dead_{n}\n")
                    out.append(f"    :mmk_ok_{n}\n")
                    junk_injected = True
                    changed = True
                i += 1
                continue
            # annotation / param / registers — PASS-THROUGH utuh
            if (
                s.startswith(".registers ") or s.startswith(".locals ")
                or s.startswith(".param") or s.startswith(".end param")
                or s.startswith(".annotation") or s.startswith(".end annotation")
                or s.startswith(".catch") or s == "" or s.startswith("#")
            ):
                out.append(line)
                i += 1
                continue
            # baris lain di awal method = instruksi → directives selesai
            directives_done = True

        # ── inject sekali di instruksi pertama (jika belum ada .prologue) ──
        if directives_done and not junk_injected and s and not s.startswith("."):
            # jangan inject di label kosong saja; inject sebelum instruksi
            if not s.startswith(":"):
                n = rnd.randint(10000, 99999)
                out.append(f"    goto :mmk_ok_{n}\n")
                out.append(f"    :mmk_dead_{n}\n")
                out.append(f"    nop\n")
                out.append(f"    goto :mmk_dead_{n}\n")
                out.append(f"    :mmk_ok_{n}\n")
                junk_injected = True
                changed = True

        # ── nop pad sebelum return (aman) ──
        if s == "return-void" or s.startswith("return-object ") or s.startswith("return-wide ") or (
            s.startswith("return ") and not s.startswith("return-void")
        ):
            for _ in range(rnd.randint(1, 2)):
                out.append("    nop\n")
            out.append(line)
            changed = True
            i += 1
            continue

        out.append(line)
        i += 1

    if not changed:
        return False
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("".join(out))
        return True
    except Exception:
        return False


def _protect_smali_high(apk_path, jar_abs):
    """Decompile → obfuscate smali high (aman) → build. Return output apk path or None."""
    work = os.path.abspath(f"_mmk_protect_smali_{int(time.time())}")
    out_apk = os.path.abspath(
        os.path.splitext(os.path.basename(apk_path))[0] + "_dexhigh.apk"
    )
    if os.path.isdir(work):
        shutil.rmtree(work, ignore_errors=True)
    banner("DEX HIGH", "Smali obfuscate AMAN (nop/opaque · skip framework)")
    info("Decode APK → smali...")
    rc = run_java_quiet(["java", "-jar", jar_abs, "d", "-i", apk_path, "-o", work, "-f"], label="DECOMPILE")
    if rc != 0 or not os.path.isdir(work):
        rc = run_java_quiet(["java", "-jar", jar_abs, "d", "-i", apk_path, "-o", work, "-f"], label="DECOMPILE")
    if rc != 0 or not os.path.isdir(work):
        err("Decompile gagal untuk smali high")
        return None
    smali_files = []
    for root, _, fs in os.walk(work):
        for fn in fs:
            if fn.endswith(".smali"):
                smali_files.append(os.path.join(root, fn))
    ok(f"{len(smali_files)} smali files")
    n = 0
    for i, fp in enumerate(smali_files, 1):
        if _smali_high_obfuscate_file(fp):
            n += 1
        if i % 400 == 0 or i == len(smali_files):
            progress_bar(i, len(smali_files), "smali high")
    ok(f"Obfuscated: {n} files (framework di-skip)")
    banner("BUILD", "APKEditor b")
    if os.path.exists(out_apk):
        try:
            os.remove(out_apk)
        except Exception:
            pass
    # coba internal dulu, lalu jf
    rc = run_java_quiet(["java", "-jar", jar_abs, "b", "-i", work, "-o", out_apk, "-f"], label="BUILD")
    if rc != 0 or not os.path.isfile(out_apk):
        warn("Build internal gagal — coba -dex-lib jf")
        rc = subprocess.call(
            ["java", "-jar", jar_abs, "b", "-i", work, "-o", out_apk, "-f", "-dex-lib", "jf"]
        )
    if rc != 0 or not os.path.isfile(out_apk):
        rc = run_java_quiet(["java", "-jar", jar_abs, "b", "-i", work, "-o", out_apk, "-f"], label="BUILD")
    # jangan hapus work jika gagal — bantu debug
    if not os.path.isfile(out_apk):
        err("Build smali high gagal")
        warn(f"Work dir disimpan: {work}")
        return None
    shutil.rmtree(work, ignore_errors=True)
    return out_apk


def _protect_dpt(apk_path, dpt_jar, safe=True):
    """
    DEX shell via dpt-shell.
    safe=True  → keep-classes + matikan anti-debug/frida/crc (kurangi stuck splash)
    safe=False → agresif penuh
    """
    banner("DPT-SHELL", "DEX shell  •  " + ("SAFE (keep-classes)" if safe else "MAX"))
    info(f"Engine: {os.path.basename(dpt_jar)}")
    info("https://github.com/luoyesiqiu/dpt-shell")
    out_dir = os.path.abspath(f"_dpt_out_{int(time.time())}")
    os.makedirs(out_dir, exist_ok=True)

    # -x  no-sign (kita sign sendiri menu 6)
    # -e  exclude x86 (APK lebih kecil, HP real = arm)
    # SAFE flags: mengurangi hang di splash / logo
    cmd = [
        "java", "-jar", dpt_jar,
        "-f", apk_path,
        "-o", out_dir,
        "-x",
        "-e", "x86,x86_64",
    ]
    if safe:
        cmd.extend([
            "-K",                      # keep-classes → startup lebih cepat
            "--disable-anti-debug",
            "--disable-frida-detect",
            "--disable-crc-detect",
        ])
        info("Flags SAFE: -K --disable-anti-debug --disable-frida --disable-crc")
    else:
        info("Flags MAX: full risk-check aktif")

    box_cmd_short("job", cmd[cmd.index("-i")+1] if "-i" in cmd else "", cmd[cmd.index("-o")+1] if "-o" in cmd else "", " ".join(cmd[3:6]) if len(cmd)>5 else "")
    try:
        rc = subprocess.call(cmd)
    except Exception as e:
        err(str(e))
        return None

    found = None
    for root, _, fs in os.walk(out_dir):
        for f in fs:
            if f.lower().endswith(".apk"):
                fp = os.path.join(root, f)
                if found is None or os.path.getsize(fp) > os.path.getsize(found):
                    found = fp
    if not found:
        auto = os.path.splitext(apk_path)[0] + "_protected.apk"
        if os.path.isfile(auto):
            found = auto
    if not found:
        err("dpt-shell tidak menghasilkan APK")
        return None
    tag = "_dpt_safe.apk" if safe else "_dpt_max.apk"
    final = os.path.abspath(os.path.splitext(os.path.basename(apk_path))[0] + tag)
    shutil.copy2(found, final)
    try:
        shutil.rmtree(out_dir, ignore_errors=True)
    except Exception:
        pass
    return final


def _cyberarmor_find_root():
    """Cari folder clone CyberArmor."""
    candidates = [
        os.path.abspath("CyberArmor"),
        os.path.abspath("cyberarmor"),
        os.path.join(str(Path.home()), "CyberArmor"),
        "/storage/emulated/0/Zbot/CyberArmor",
        "/storage/emulated/0/CyberArmor",
    ]
    for c in candidates:
        if os.path.isdir(c) and (
            os.path.isfile(os.path.join(c, "settings.gradle.kts"))
            or os.path.isdir(os.path.join(c, "packer-cli"))
        ):
            return c
    return None


def _cyberarmor_find_cli(root):
    """Path ke binary cyberarmor (installDist)."""
    if not root:
        return None
    paths = [
        os.path.join(root, "packer-cli", "build", "install", "cyberarmor", "bin", "cyberarmor"),
        os.path.join(root, "packer-cli", "build", "install", "cyberarmor", "bin", "cyberarmor.bat"),
    ]
    # juga di PATH
    which = shutil.which("cyberarmor")
    if which:
        return which
    for p in paths:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
        if os.path.isfile(p):
            return p
    return None


def _cyberarmor_artifacts(root):
    """Return dict stub_dex, shell_arm64, shell_arm32 atau partial."""
    out = {"stub": None, "arm64": None, "arm32": None, "root": root}
    if not root:
        return out
    stub = os.path.join(root, "shell-stub", "build", "classes.dex")
    if os.path.isfile(stub):
        out["stub"] = stub
    a64 = os.path.join(root, "shell-native", "build", "arm64-v8a", "libcyberarmor.so")
    a32 = os.path.join(root, "shell-native", "build", "armeabi-v7a", "libcyberarmor.so")
    if os.path.isfile(a64):
        out["arm64"] = a64
    if os.path.isfile(a32):
        out["arm32"] = a32
    # fallback cari di tree
    if not out["stub"] or not out["arm64"]:
        for dirpath, _, files in os.walk(root):
            for f in files:
                fp = os.path.join(dirpath, f)
                if f == "classes.dex" and "shell-stub" in dirpath.replace("\\", "/") and not out["stub"]:
                    out["stub"] = fp
                if f == "libcyberarmor.so":
                    if "arm64" in dirpath and not out["arm64"]:
                        out["arm64"] = fp
                    if "armeabi" in dirpath or "arm32" in dirpath or "v7a" in dirpath:
                        if not out["arm32"]:
                            out["arm32"] = fp
    return out


def _cyberarmor_print_setup(root=None):
    """Tampilkan instruksi build CyberArmor."""
    print()
    banner("CYBERARMOR SETUP", "https://github.com/VexoraWebServices/CyberArmor")
    info("Butuh: JDK 21 + Android SDK build-tools + NDK + Gradle (bukan ringan di Termux)")
    print(f"  {C.DIM}1. git clone https://github.com/VexoraWebServices/CyberArmor.git{C.RESET}")
    print(f"  {C.DIM}2. cd CyberArmor && buat local.properties (sdk.dir=...){C.RESET}")
    print(f"  {C.DIM}3. ./shell-native/build-native.sh{C.RESET}")
    print(f"  {C.DIM}4. ./shell-stub/build-stub.sh{C.RESET}")
    print(f"  {C.DIM}5. ./gradlew :packer-cli:installDist{C.RESET}")
    print(f"  {C.DIM}6. keytool -genkeypair ... keys/cyberarmor.jks{C.RESET}")
    if root:
        info(f"Root terdeteksi: {root}")
        art = _cyberarmor_artifacts(root)
        info(f"  stub-dex : {'OK' if art['stub'] else 'MISSING'}")
        info(f"  shell-arm64: {'OK' if art['arm64'] else 'MISSING'}")
        info(f"  shell-arm32: {'OK' if art['arm32'] else 'MISSING'}")
        cli = _cyberarmor_find_cli(root)
        info(f"  CLI      : {cli or 'MISSING — jalankan installDist'}")


def _protect_cyberarmor(apk_path, profile="default"):
    """
    Hardening via CyberArmor CLI.
    https://github.com/VexoraWebServices/CyberArmor
    """
    banner("CYBERARMOR", f"profile={profile} · DEX encrypt + RASP")
    info("https://github.com/VexoraWebServices/CyberArmor")

    root = _cyberarmor_find_root()
    if not root:
        warn("Folder CyberArmor tidak ketemu di cwd / ~/CyberArmor")
        ans = input(f"  {C.CYAN}Clone sekarang? [Y/n]{C.RESET} ➤ ").strip().lower()
        if ans not in ("n", "no", "tidak"):
            spinner("git clone CyberArmor...", 0.5)
            rc = subprocess.call(
                ["git", "clone", "--depth", "1",
                 "https://github.com/VexoraWebServices/CyberArmor.git", "CyberArmor"]
            )
            if rc == 0:
                root = os.path.abspath("CyberArmor")
            else:
                err("Clone gagal")
                _cyberarmor_print_setup()
                return None
        else:
            _cyberarmor_print_setup()
            return None

    art = _cyberarmor_artifacts(root)
    cli = _cyberarmor_find_cli(root)
    if not cli or not art.get("stub") or not art.get("arm64"):
        err("CyberArmor belum di-build lengkap")
        _cyberarmor_print_setup(root)
        return None

    ok(f"CLI : {cli}")
    ok(f"Stub: {art['stub']}")
    ok(f"SO  : {art['arm64']}")

    # keystore
    ks = None
    for cand in (
        os.path.join(root, "keys", "cyberarmor.jks"),
        os.path.abspath("cyberarmor.jks"),
        os.path.abspath("debug.jks"),
    ):
        if os.path.isfile(cand):
            ks = cand
            break
    keys = []
    try:
        for f in os.listdir("."):
            if f.lower().endswith((".jks", ".keystore")):
                keys.append(os.path.abspath(f))
    except Exception:
        pass
    if not ks and keys:
        ks = keys[0]

    storepass = os.environ.get("MMK_KS_PASS") or os.environ.get("CYBERARMOR_KS_PASS") or "changeit"
    alias = os.environ.get("MMK_KEY_ALIAS") or os.environ.get("CYBERARMOR_KS_ALIAS") or "cyberarmor"
    if ks and "debug" in os.path.basename(ks).lower():
        storepass = os.environ.get("MMK_KS_PASS") or "android"
        alias = os.environ.get("MMK_KEY_ALIAS") or "androiddebugkey"

    out_apk = mmk_output("protect", os.path.splitext(os.path.basename(apk_path))[0] + f"_cyberarmor_{profile}.apk")
    if os.path.exists(out_apk):
        try:
            os.remove(out_apk)
        except Exception:
            pass

    cmd = [
        cli,
        "-i", apk_path,
        "-o", out_apk,
        "--stub-dex", art["stub"],
        "--shell-arm64", art["arm64"],
        "--protection", profile,
    ]
    if art.get("arm32"):
        cmd.extend(["--shell-arm32", art["arm32"]])
    if ks:
        cmd.extend(["--ks", ks, "--ks-pass", storepass, "--ks-alias", alias])
        ok(f"Keystore: {os.path.basename(ks)}")
    else:
        warn("Tanpa keystore — output unsigned (debug only)")

    # optional flags from user env
    if os.environ.get("CYBERARMOR_PROTECT_SO"):
        cmd.append("--protect-so")
    if os.environ.get("CYBERARMOR_ANTI_PTRACE"):
        cmd.append("--anti-ptrace")

    info("CMD: " + " ".join(cmd[:8]) + " ...")
    spinner("CyberArmor harden (bisa lama)...", 1.5)
    try:
        rc = subprocess.call(cmd)
    except Exception as e:
        err(f"Gagal jalankan cyberarmor: {e}")
        return None
    if rc != 0 or not os.path.isfile(out_apk):
        err(f"CyberArmor gagal (code {rc})")
        info("Cek JDK21 + build artifacts + log di atas")
        return None
    ok(f"Hardened: {os.path.basename(out_apk)}")
    return out_apk



def _ensure_dalvik_obfuscator():
    """Clone thuxnder/dalvik-obfuscator ke files/ jika belum ada."""
    dest = os.path.join(MMK_FILES_DIR, "dalvik-obfuscator")
    if os.path.isfile(os.path.join(dest, "baksmali-modifier.py")):
        return dest
    mmk_ensure_dirs()
    banner("DALVIK-OBFUSCATOR", "git clone thuxnder/dalvik-obfuscator")
    warn("RESEARCH ONLY — bisa merusak app (peringatan resmi upstream)")
    if not shutil.which("git"):
        err("git diperlukan")
        return None
    try:
        rc = subprocess.call(
            ["git", "clone", "--depth", "1",
             "https://github.com/thuxnder/dalvik-obfuscator.git", dest]
        )
        if rc == 0 and os.path.isdir(dest):
            ok(f"Cloned: {dest}")
            return dest
    except Exception as e:
        err(str(e))
    return None


def _dalvik_nop_inject_smali(dec_dir, max_files=5000):
    """
    Inspirasi baksmali-modifier.py (thuxnder/dalvik-obfuscator):
    sisipkan nop setelah instruksi tertentu agar decompiler bingung.
    Versi aman-terbatas (bukan full research crackme).
    """
    smali_files = []
    for root, _, fs in os.walk(dec_dir):
        for fn in fs:
            if fn.endswith(".smali"):
                smali_files.append(os.path.join(root, fn))
    ok(f"{len(smali_files)} smali files")
    changed = 0
    # instruksi yang aman disisipi nop setelahnya
    safe_ops = re.compile(
        r"^([ \t]+)(const(?:/\d+)?|move(?:-\w+)?|add-\w+|sub-\w+|mul-\w+|div-\w+|"
        r"and-\w+|or-\w+|xor-\w+|shl-\w+|shr-\w+|iget(?:-\w+)?|iput(?:-\w+)?|"
        r"sget(?:-\w+)?|sput(?:-\w+)?|aget(?:-\w+)?|aput(?:-\w+)?)\b.*$"
    )
    for i, fp in enumerate(smali_files):
        if i >= max_files:
            break
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            continue
        out = []
        file_hit = 0
        in_method = False
        for ln in lines:
            if ln.strip().startswith(".method"):
                in_method = True
            elif ln.strip().startswith(".end method"):
                in_method = False
            out.append(ln)
            if in_method and safe_ops.match(ln) and file_hit < 40:
                # sisip 1 nop (indent sama)
                indent = re.match(r"^([ \t]*)", ln).group(1)
                out.append(f"{indent}nop\n")
                file_hit += 1
        if file_hit:
            try:
                with open(fp, "w", encoding="utf-8") as f:
                    f.writelines(out)
                changed += 1
            except Exception:
                pass
        if (i + 1) % 200 == 0 or i + 1 == len(smali_files):
            progress_bar(i + 1, min(len(smali_files), max_files), "dalvik nop")
    return changed


def _protect_dalvik_obfuscator(apk_path, jar_abs):
    """
    Pipeline mirip obfuscate.sh (research):
    decompile → nop inject smali → rebuild → optional APKEditor protect resource
    Ref: https://github.com/thuxnder/dalvik-obfuscator
    """
    warn("Dalvik-obfuscator = RESEARCH — risiko app crash / ANR")
    _ensure_dalvik_obfuscator()  # optional clone scripts
    base = os.path.splitext(os.path.basename(apk_path))[0]
    work_out = os.path.abspath(f"{base}_dalvik_obf.apk")
    dest = mmk_output("protect", f"{base}_dalvik_obf.apk")
    dec = os.path.abspath(f"_dalvik_obf_{base}_dec")
    if os.path.isdir(dec):
        shutil.rmtree(dec, ignore_errors=True)
    for pth in (work_out, dest):
        if os.path.exists(pth):
            try:
                os.remove(pth)
            except Exception:
                pass

    banner("DECOMPILE", "APKEditor d")
    box_cmd_short("decompile", apk_path, dec, "dalvik-obf")
    rc = run_java_quiet(["java", "-jar", jar_abs, "d", "-i", apk_path, "-o", dec, "-f"], label="DECOMPILE")
    if rc != 0 or not os.path.isdir(dec):
        err("Decompile gagal")
        return None

    banner("NOP INJECT", "baksmali-modifier style (research)")
    n = _dalvik_nop_inject_smali(dec)
    ok(f"Files patched: {n}")

    banner("BUILD", "APKEditor b")
    box_cmd_short("build", dec, work_out, "dalvik-obf")
    rc = run_java_quiet(["java", "-jar", jar_abs, "b", "-i", dec, "-o", work_out, "-f"], label="BUILD")
    shutil.rmtree(dec, ignore_errors=True)
    if not os.path.isfile(work_out):
        run_java_quiet_show_errors()
        err("Build gagal")
        return None
    try:
        shutil.move(work_out, dest)
        out = dest
    except Exception:
        out = work_out
    ok(f"Output: {os.path.basename(out)}")
    return out


def _ensure_proguard():
    """
    Pastikan ProGuard tersedia.
    Cari proguard.jar di files/, atau unduh release dari GitHub Guardsquare.
    """
    found = mmk_find_in_files("proguard.jar", "proguard*.jar", "*/lib/proguard.jar")
    if found:
        return found[0]
    # scripts
    for root in (MMK_FILES_DIR, os.getcwd()):
        for name in ("proguard.sh", "proguard.bat"):
            fp = os.path.join(root, "proguard", "bin", name)
            if os.path.isfile(fp):
                return fp
    mmk_ensure_dirs()
    banner("PROGUARD", "download Guardsquare release")
    info("https://github.com/Guardsquare/proguard/releases")
    dest_dir = os.path.join(MMK_FILES_DIR, "proguard")
    try:
        import json as _json
        api = "https://api.github.com/repos/Guardsquare/proguard/releases/latest"
        req = urllib.request.Request(api, headers={"User-Agent": "MMK-MOD/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = _json.load(resp)
        url = None
        fname = "proguard.zip"
        for asset in data.get("assets", []):
            n = asset.get("name", "")
            if n.endswith(".zip") or "proguard" in n.lower() and n.endswith(".jar"):
                url = asset["browser_download_url"]
                fname = n
                break
        if not url:
            # fallback known pattern - maven style not zip
            err("Tidak menemukan asset release — install manual")
            info("Taruh proguard.jar di folder files/")
            return None
        zip_path = os.path.join(MMK_FILES_DIR, fname)
        spinner(f"Download {fname}...", 1.0)
        req = urllib.request.Request(url, headers={"User-Agent": "MMK-MOD/1.0"})
        with urllib.request.urlopen(req, timeout=180) as resp, open(zip_path, "wb") as f:
            shutil.copyfileobj(resp, f)
        if zip_path.endswith(".zip"):
            os.makedirs(dest_dir, exist_ok=True)
            shutil.unpack_archive(zip_path, dest_dir)
            # find jar
            for root, _, fs in os.walk(dest_dir):
                for fn in fs:
                    if fn == "proguard.jar" or (fn.startswith("proguard") and fn.endswith(".jar")):
                        return os.path.join(root, fn)
        elif zip_path.endswith(".jar"):
            return zip_path
    except Exception as e:
        err(f"Download ProGuard gagal: {e}")
        info("Manual: https://github.com/Guardsquare/proguard/releases")
        info(f"Taruh proguard.jar di {MMK_FILES_DIR}")
    return None


def _protect_proguard(apk_path):
    """
    ProGuard (Guardsquare) — shrink/optimize/obfuscate.
    https://github.com/Guardsquare/proguard
    Alur: ProGuard -injars apk -outjars out -android + keep rules aman.
    """
    if not shutil.which("java"):
        err("Java diperlukan")
        return None
    pg = _ensure_proguard()
    if not pg:
        return None
    base = os.path.splitext(os.path.basename(apk_path))[0]
    work_out = os.path.abspath(f"{base}_proguard.apk")
    dest = mmk_output("protect", f"{base}_proguard.apk")
    for pth in (work_out, dest):
        if os.path.exists(pth):
            try:
                os.remove(pth)
            except Exception:
                pass

    # config file
    cfg = os.path.abspath("_mmk_proguard.pro")
    cfg_body = f"""\
-injars {apk_path}
-outjars {work_out}
-android
-dontpreverify
-dontoptimize
-dontshrink
-dontwarn **
-ignorewarnings
-keepattributes *Annotation*,Signature,InnerClasses,EnclosingMethod
-keep public class * extends android.app.Activity
-keep public class * extends android.app.Application
-keep public class * extends android.app.Service
-keep public class * extends android.content.BroadcastReceiver
-keep public class * extends android.content.ContentProvider
-keep public class * extends android.preference.Preference
-keep class androidx.** {{ *; }}
-keep class android.support.** {{ *; }}
-keepclassmembers class * {{
    public <init>(android.content.Context);
    public <init>(android.content.Context, android.util.AttributeSet);
    public <init>(android.content.Context, android.util.AttributeSet, int);
}}
-keepclassmembers enum * {{
    public static **[] values();
    public static ** valueOf(java.lang.String);
}}
"""
    with open(cfg, "w", encoding="utf-8") as f:
        f.write(cfg_body)

    banner("PROGUARD", "Guardsquare · rename obfuscation")
    box_cmd_short("proguard", apk_path, work_out, "android + keep Activity")
    if pg.endswith(".jar"):
        cmd = ["java", "-jar", pg, f"@{cfg}"]
    elif pg.endswith(".sh"):
        cmd = ["bash", pg, f"@{cfg}"]
    else:
        cmd = ["java", "-jar", pg, f"@{cfg}"]
    info(f"Tool: {pg}")
    rc = run_java_quiet(cmd, label="PROGUARD")
    try:
        os.remove(cfg)
    except Exception:
        pass

    found = None
    for c in (work_out, dest):
        if c and os.path.isfile(c) and os.path.getsize(c) > 1000:
            found = c
            break
    if not found:
        run_java_quiet_show_errors()
        err("ProGuard gagal — cek libraryjars / rules")
        info("ProGuard lebih stabil untuk JAR; APK butuh rules lengkap")
        return None
    try:
        if os.path.abspath(found) != os.path.abspath(dest):
            shutil.move(found, dest)
        out = dest
    except Exception:
        out = found
    ok(f"Output: {os.path.basename(out)}")
    return out




def _protect_list_scripts(exts):
    """List .py / .js / .html dari app/ + cwd + files/."""
    out = []
    dirs = []
    for d in (MMK_APP_DIR, MMK_FILES_DIR, os.getcwd()):
        if d and os.path.isdir(d) and d not in dirs:
            dirs.append(d)
    for d in dirs:
        try:
            for f in sorted(os.listdir(d)):
                low = f.lower()
                if any(low.endswith(e) for e in exts):
                    fp = os.path.join(d, f)
                    if os.path.isfile(fp):
                        try:
                            sz = os.path.getsize(fp)
                        except OSError:
                            sz = 0
                        label = f if d == os.getcwd() else f"{os.path.basename(d)}/{f}"
                        out.append((os.path.abspath(fp), label, sz))
        except OSError:
            pass
    # dedupe by abspath
    seen = set()
    uniq = []
    for a, b, c in out:
        if a not in seen:
            seen.add(a)
            uniq.append((a, b, c))
    return uniq


def _js_protect(source: str, level: int = 1) -> str:
    """
    Proteksi JS ringan–sedang.
    L1: minify + hapus komentar
    L2: + bungkus eval(atob(...))
    L3: + layer base64 ganda + anti-format sederhana
    """
    import re as _re
    import base64 as _b64
    s = source
    # hapus /* */ dan // komentar (sederhana)
    s = _re.sub(r"/\*[\s\S]*?\*/", "", s)
    s = _re.sub(r"(?m)^\s*//.*?$", "", s)
    s = _re.sub(r"(?m)([^:])//.*?$", r"\1", s)
    # minify whitespace
    s = _re.sub(r"\s+", " ", s).strip()
    if level <= 1:
        return f"/* MMK MOD L1 */\n{s}\n"
    raw = s.encode("utf-8")
    b1 = _b64.b64encode(raw).decode("ascii")
    if level == 2:
        return (
            "/* MMK MOD L2 · protected */\n"
            "(function(){try{eval(atob('%s'));}catch(e){}})();\n" % b1
        )
    # L3 double
    b2 = _b64.b64encode(b1.encode("ascii")).decode("ascii")
    return (
        "/* MMK MOD L3 · protected */\n"
        "(function(_0x){try{eval(atob(atob(_0x)));}catch(_e){}})('%s');\n" % b2
    )


def _html_protect(source: str, level: int = 1) -> str:
    """
    Proteksi HTML.
    L1: minify (hapus komentar + whitespace berlebih)
    L2: minify + obfuscate inline <script>
    L3: L2 + bungkus body dalam decoder sederhana
    """
    import re as _re
    s = source
    # hapus komentar HTML
    s = _re.sub(r"<!--[\s\S]*?-->", "", s)
    if level >= 2:
        def _scr(m):
            inner = m.group(1)
            if not inner.strip():
                return m.group(0)
            prot = _js_protect(inner, level=min(level, 3))
            return "<script>%s</script>" % prot
        s = _re.sub(
            r"<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)</script>",
            _scr,
            s,
            flags=_re.I,
        )
    # minify antar tag
    s = _re.sub(r">\s+<", "><", s)
    s = _re.sub(r"\s{2,}", " ", s).strip()
    if level >= 3:
        # optional: tidak break HTML structure terlalu jauh — hanya tandai
        s = "<!-- MMK MOD HTML L3 -->\n" + s
    else:
        s = "<!-- MMK MOD HTML L%d -->\n" % level + s
    return s


def _py_protect_simple(source: str, level: int = 1) -> str:
    """
    Proteksi .py — pakai layer marshal Py-Fuscate (level = jumlah layer).
    level 1 → 10 layers, 2 → 30, 3 → 50 (cepat di Termux).
    """
    layers = {1: 10, 2: 30, 3: 50}.get(level, 10)
    encoded = source
    for _ in range(layers):
        encoded = _pyfuscate_encode_once(encoded)
    py_ver = "python" + ".".join(str(x) for x in sys.version_info[:2])
    return (
        f"# Encoded By MMK MOD · Protect Script L{level}\n"
        f"# Layers: {layers}\n"
        f"# Run with {py_ver}\n"
        f"try:\n\t{encoded}\nexcept KeyboardInterrupt:\n\texit()\n"
    )


def protect_script_main():
    """
    Proteksi file .py / .js / .html (bukan APK).
    """
    banner("PROTECT SCRIPT", ".py · .js · .html")
    print()
    print(f"  {C.CYAN}┌────┬────────┬────────────────────────────────────┐{C.RESET}")
    print(f"  {C.CYAN}│{C.RESET}{C.YELLOW} NO {C.RESET}{C.CYAN}│{C.RESET}{C.YELLOW} TIPE   {C.RESET}{C.CYAN}│{C.RESET}{C.YELLOW} KETERANGAN                       {C.RESET}{C.CYAN}│{C.RESET}")
    print(f"  {C.CYAN}├────┼────────┼────────────────────────────────────┤{C.RESET}")
    for no, tip, ket in (
        ("1", ".py", "Marshal layers (Py-Fuscate)"),
        ("2", ".js", "Minify + base64 / eval(atob)"),
        ("3", ".html", "Minify + obfuscate inline JS"),
        ("4", "Semua", "Scan folder · pilih file campuran"),
        ("0", "Exit", "Kembali"),
    ):
        col = C.GREEN if no != "0" else C.RED
        print(f"  {C.CYAN}│{C.RESET}{col} {no:^2} {C.RESET}{C.CYAN}│{C.RESET} {tip:<6} {C.CYAN}│{C.RESET} {ket:<34} {C.CYAN}│{C.RESET}")
    print(f"  {C.CYAN}└────┴────────┴────────────────────────────────────┘{C.RESET}")
    tip = input(f"  {C.MAGENTA}Pilih tipe ➤{C.RESET} ").strip()
    if tip in ("0", "", "q"):
        return
    if tip == "1":
        exts = (".py",)
    elif tip == "2":
        exts = (".js",)
    elif tip == "3":
        exts = (".html", ".htm")
    elif tip == "4":
        exts = (".py", ".js", ".html", ".htm")
    else:
        err("Pilihan tidak valid")
        return

    entries = _protect_list_scripts(exts)
    if not entries:
        err(f"Tidak ada file {exts} di app/ / files/ / cwd")
        return
    chosen = select_target(entries, title="SELECT FILE  ·  PROTECT SCRIPT")
    if not chosen:
        return
    ok(f"Target: {os.path.basename(chosen)}")

    print()
    print(f"  {C.CYAN}┌────┬────────┬──────────────────────────────┐{C.RESET}")
    print(f"  {C.CYAN}│{C.RESET}{C.YELLOW} LV {C.RESET}{C.CYAN}│{C.RESET}{C.YELLOW} NAMA   {C.RESET}{C.CYAN}│{C.RESET}{C.YELLOW} EFEK                         {C.RESET}{C.CYAN}│{C.RESET}")
    print(f"  {C.CYAN}├────┼────────┼──────────────────────────────┤{C.RESET}")
    for a, b, c in (
        ("1", "LOW", "Minify / 10 layer py"),
        ("2", "MID", "Base64 + minify / 30 layer"),
        ("3", "HIGH", "Double encode / 50 layer"),
    ):
        print(f"  {C.CYAN}│{C.RESET}{C.GREEN} {a:^2} {C.RESET}{C.CYAN}│{C.RESET} {b:<6} {C.CYAN}│{C.RESET} {c:<28} {C.CYAN}│{C.RESET}")
    print(f"  {C.CYAN}└────┴────────┴──────────────────────────────┘{C.RESET}")
    lv_s = input(f"  {C.MAGENTA}Level [1-3] default 2 ➤{C.RESET} ").strip() or "2"
    if not lv_s.isdigit() or not (1 <= int(lv_s) <= 3):
        level = 2
    else:
        level = int(lv_s)

    try:
        with open(chosen, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception as e:
        err(f"Gagal baca: {e}")
        return
    if not source.strip():
        err("File kosong")
        return

    low = chosen.lower()
    stem = os.path.splitext(os.path.basename(chosen))[0]
    if low.endswith(".py"):
        banner("PROTECT PY", f"L{level}")
        out_name = f"{stem}-enc.py"
        try:
            result = _py_protect_simple(source, level)
        except Exception as e:
            err(f"Py protect gagal: {e}")
            return
    elif low.endswith(".js"):
        banner("PROTECT JS", f"L{level}")
        out_name = f"{stem}-enc.js"
        result = _js_protect(source, level)
    elif low.endswith((".html", ".htm")):
        banner("PROTECT HTML", f"L{level}")
        out_name = f"{stem}-enc.html"
        result = _html_protect(source, level)
    else:
        err("Ekstensi tidak didukung")
        return

    # simpan ke out/protect (script) — fallback cwd
    dest = mmk_output("protect", out_name)
    work = os.path.abspath(out_name)
    saved = None
    for path_out in (dest, work):
        try:
            parent = os.path.dirname(path_out)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(path_out, "w", encoding="utf-8") as f:
                f.write(result)
            ok(f"Saved: {path_out} ({human_size(os.path.getsize(path_out))})")
            saved = path_out
            break
        except Exception as e:
            warn(str(e))
            continue
    if not saved:
        err("Gagal tulis output")
        return

    out_dir = os.path.dirname(os.path.abspath(saved)) or os.getcwd()
    box_info(
        [
            f"✔  Input  : {os.path.basename(chosen)}",
            f"✔  Output : {os.path.basename(saved)}",
            f"✔  Level  : {level}",
            f"✔  Size   : {human_size(os.path.getsize(saved))}",
            f"✔  Direktori : {out_dir}",
        ],
        title="PROTECT SCRIPT DONE",
    )
    # tabel ringkas
    print()
    print(f"  {C.CYAN}┌──────────────┬──────────────────────────────────────────┐{C.RESET}")
    print(f"  {C.CYAN}│{C.RESET} File         {C.CYAN}│{C.RESET} {os.path.basename(saved):<40} {C.CYAN}│{C.RESET}")
    print(f"  {C.CYAN}│{C.RESET} Direktori    {C.CYAN}│{C.RESET} {out_dir[:40]:<40} {C.CYAN}│{C.RESET}")
    if len(out_dir) > 40:
        print(f"  {C.CYAN}│{C.RESET}              {C.CYAN}│{C.RESET} {out_dir[40:80]:<40} {C.CYAN}│{C.RESET}")
    print(f"  {C.CYAN}└──────────────┴──────────────────────────────────────────┘{C.RESET}")


def _dex_clean_smali_content(content, level=2):
    """
    Bersihkan smali dari pola 'kebingungan' (obfuscation junk).
    level 1: hapus nop beruntun + baris kosong berlebih
    level 2: + hapus .line/.local verbose
    level 3: + hapus goto/label junk sederhana (hati-hati)
    """
    lines = content.splitlines(keepends=True)
    out = []
    prev_nop = 0
    n_nop = n_dbg = n_junk = 0
    for ln in lines:
        s = ln.strip()
        # nop chain
        if s == "nop":
            prev_nop += 1
            if level >= 1 and prev_nop > 1:
                n_nop += 1
                continue
            if level >= 3 and prev_nop >= 1:
                n_nop += 1
                continue
            out.append(ln)
            continue
        prev_nop = 0
        # debug
        if level >= 2 and (
            s.startswith(".line ")
            or s.startswith(".local ")
            or s.startswith(".end local")
            or s.startswith(".param ")
        ):
            n_dbg += 1
            continue
        # junk: empty labels yang tidak dipakai sulit — skip
        # hapus const yang langsung di-overwrite pola klasik: const/4 vX, 0x0 \n const/4 vX, 0x1
        out.append(ln)
    text = "".join(out)
    if level >= 1:
        text2 = re.sub(r"\n{3,}", "\n\n", text)
        if text2 != text:
            n_junk += text.count("\n\n\n")
            text = text2
    return text, n_nop, n_dbg, n_junk


def dex_anti_confusion_main():
    """
    DEX Anti-Kebingungan — bersihkan junk obfuscation di smali/DEX.
    Bukan unpack packer native; fokus: nop spam, debug noise, whitespace.
    Input: menu/app  ·  Output: menu/out/patched
    """
    banner("DEX ANTI-KEBINGUNGAN", "bersihkan junk obfuscation · smali clean")
    info("Mengurangi 'kebingungan' hasil confuser (nop / debug / noise)")
    warn("Tidak membuka packer native (DPT/CyberArmor shell)")
    print()

    print(f"  {C.CYAN}┌────┬────────┬────────────────────────────────────────┐{C.RESET}")
    print(f"  {C.CYAN}│{C.RESET}{C.YELLOW} LV {C.RESET}{C.CYAN}│{C.RESET}{C.YELLOW} NAMA   {C.RESET}{C.CYAN}│{C.RESET}{C.YELLOW} EFEK                                  {C.RESET}{C.CYAN}│{C.RESET}")
    print(f"  {C.CYAN}├────┼────────┼────────────────────────────────────────┤{C.RESET}")
    for a, b, c in (
        ("1", "RINGAN", "Hapus NOP beruntun + rapikan baris"),
        ("2", "SEDANG", "RINGAN + strip .line/.local debug"),
        ("3", "AGRESIF", "SEDANG + hapus hampir semua NOP"),
        ("0", "EXIT", "Kembali"),
    ):
        col = C.GREEN if a != "0" else C.RED
        print(f"  {C.CYAN}│{C.RESET}{col} {a:^2} {C.RESET}{C.CYAN}│{C.RESET} {b:<6} {C.CYAN}│{C.RESET} {c:<38} {C.CYAN}│{C.RESET}")
    print(f"  {C.CYAN}└────┴────────┴────────────────────────────────────────┘{C.RESET}")

    preset = (globals().get("MMK_PRESET_OPTIONS") or {}).get("21")
    if preset in ("1", "2", "3"):
        lv = preset
        ok(f"Level preset (multibypass): {lv}")
    else:
        lv = input(f"  {C.MAGENTA}Level [1-3] default 2 ➤{C.RESET} ").strip() or "2"
    if lv in ("0", "q"):
        return
    if lv not in ("1", "2", "3"):
        lv = "2"
    level = int(lv)

    entries = mmk_list_apks((".apk", ".apks", ".xapk"))
    if not entries:
        err(f"Tidak ada APK di {MMK_APP_DIR}")
        info("Letakkan APK di menu/app/")
        return
    apk_path = select_target(entries, title="SELECT APK  ·  DEX ANTI-BINGUNG") if "select_target" in globals() else entries[0][0]
    if not apk_path:
        return
    ok(f"Target: {os.path.basename(apk_path)}")

    if not shutil.which("java"):
        err("Java diperlukan")
        return
    jar = None
    for finder in ("_smali_ensure_apkeditor", "_find_or_fetch_apkeditor", "_smali_find_apkeditor"):
        if finder in globals():
            try:
                jar = globals()[finder]()
            except Exception:
                jar = None
            if jar:
                break
    if not jar:
        err("APKEditor.jar diperlukan")
        info(f"Letakkan di: {MMK_FILES_DIR}")
        return
    jar = os.path.abspath(jar)

    # merge apks
    if apk_path.lower().endswith((".apks", ".xapk")):
        merged = os.path.splitext(apk_path)[0] + "_merged.apk"
        run_java_quiet(["java", "-jar", jar, "m", "-i", apk_path, "-o", merged, "-f"], label="MERGE")
        if os.path.isfile(merged):
            apk_path = merged
            ok(f"Merged: {os.path.basename(apk_path)}")
        else:
            err("Merge gagal")
            return

    base = os.path.splitext(os.path.basename(apk_path))[0]
    dec = os.path.abspath(f"_dexclean_{base}_dec")
    work_out = os.path.abspath(f"{base}_anticnf_L{level}.apk")
    dest = mmk_output("patched", f"{base}_anticnf_L{level}.apk")
    if os.path.isdir(dec):
        shutil.rmtree(dec, ignore_errors=True)
    for pth in (work_out, dest):
        if os.path.exists(pth):
            try:
                os.remove(pth)
            except Exception:
                pass

    banner("DECOMPILE", f"level clean {level}")
    box_cmd_short("decompile", apk_path, dec, f"anti-confusion L{level}")
    rc = run_java_quiet(["java", "-jar", jar, "d", "-i", apk_path, "-o", dec, "-f"], label="DECOMPILE")
    if rc != 0 or not os.path.isdir(dec):
        err("Decompile gagal")
        run_java_quiet_show_errors()
        return

    banner("CLEAN SMALI", f"anti-kebingungan L{level}")
    total_files = nop_n = dbg_n = junk_n = changed_files = 0
    for root, _, fs in os.walk(dec):
        for fn in fs:
            if not fn.endswith(".smali"):
                continue
            total_files += 1
            fp = os.path.join(root, fn)
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    src = f.read()
            except Exception:
                continue
            new, a, b, c = _dex_clean_smali_content(src, level)
            if new != src:
                try:
                    with open(fp, "w", encoding="utf-8") as f:
                        f.write(new)
                    changed_files += 1
                    nop_n += a
                    dbg_n += b
                    junk_n += c
                except Exception:
                    pass
            if total_files % 400 == 0:
                progress_live(min(95, total_files / 50), f"smali {total_files}")
    print()
    box_info([
        f"Smali files : {total_files}",
        f"Modified    : {changed_files}",
        f"NOP removed : {nop_n}",
        f"Debug strip : {dbg_n}",
        f"Level       : {level}",
    ], title="CLEAN STATS")

    banner("BUILD", "recompile APK")
    box_cmd_short("build", dec, work_out, f"anticnf L{level}")
    rc = run_java_quiet(["java", "-jar", jar, "b", "-i", dec, "-o", work_out, "-f"], label="BUILD")
    if rc != 0 or not os.path.isfile(work_out) or os.path.getsize(work_out) < 1000:
        err("Build gagal")
        run_java_quiet_show_errors()
        return
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if os.path.abspath(work_out) != os.path.abspath(dest):
            shutil.move(work_out, dest)
        out = dest
    except Exception:
        out = work_out

    shutil.rmtree(dec, ignore_errors=True)
    out_dir = os.path.dirname(os.path.abspath(out)) or os.getcwd()
    print()
    print(f"  {C.MAGENTA}╔{'═'*58}╗{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}{C.BOLD}{C.GREEN}{'DEX ANTI-KEBINGUNGAN DONE'.center(58)}{C.RESET}{C.MAGENTA}║{C.RESET}")
    print(f"  {C.MAGENTA}╠{'═'*58}╣{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  Output    : {C.CYAN}{os.path.basename(out)}{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  Level     : L{level}")
    print(f"  {C.MAGENTA}║{C.RESET}  Size      : {human_size(os.path.getsize(out))}")
    print(f"  {C.MAGENTA}║{C.RESET}  Direktori : {C.CYAN}{out_dir[:44]}{C.RESET}")
    print(f"  {C.MAGENTA}╚{'═'*58}╝{C.RESET}")
    warn("Sign ulang (menu 6) sebelum install")
    try:
        if "mmk_history_add" in globals():
            mmk_history_add(
                "dex_anticnf",
                out,
                extra={"ok": 1, "steps": f"anti-confusion L{level}", "steps_detail": [f"nop={nop_n}", f"dbg={dbg_n}"]},
            )
    except Exception:
        pass





# ═══════════════════════════════════════════════════════════════
#  PREMIUM LOGIC SCAN (embedded — identify only, high-accuracy)
# ═══════════════════════════════════════════════════════════════

# Nama kuat (jarang false positive)
_MMK_PREMIUM_STRONG_RE = re.compile(
    r"(?i)("
    r"ispremium|is_premium|getpremium|haspremium|setpremium|premiumstatus|"
    r"premium_is_active|checkpremium|"
    r"isvip|is_vip|getvip|hasvip|issvip|svipstate|"
    r"isprouser|is_pro_user|proversion|isproversion|haspro|getpro\b|"
    r"issubscribed|is_subscribed|hassubscription|getsubscription|"
    r"checksubscription|subscriptionstatus|issubscriber|"
    r"ispurchased|haspurchased|ispurchased|ispaid|isunlocked|"
    r"noads|no_ads|adfree|ad_free|removeads|adsdisabled|ads_disabled|"
    r"entitlementinfo|customerinfo|pro_access|pro_access_life|"
    r"isplus|iselite|islifetime|haslifetime|"
    r"billingclient|inapppurchase|sku_details"
    r")"
)

# Nama sedang — butuh konteks tambahan
_MMK_PREMIUM_MED_RE = re.compile(
    r"(?i)\b("
    r"premium|subscription|subscribe|purchased|entitlement|"
    r"lifetime|billing|inapp|iap\b"
    r")\b"
)

# Blacklist potongan yang sering salah (progress, product, profile, …)
_MMK_PREMIUM_FALSE = re.compile(
    r"(?i)("
    r"progress|product|profile|project|protocol|provide|provider|proxy|"
    r"process|problem|property|protection|proposal|promote|promotion|"
    r"probability|probe|proc\b|proof|province|provision|"
    r"vipers?|viper\b|goldfish|golden|goldberg|"
    r"enterprise\.android|androidx\.|support\.v4"
    r")"
)

_MMK_PREMIUM_STRING_RE = re.compile(
    r'const-string(?:/jumbo)?\s+[vp]\d+\s*,\s*"(?P<s>[^"]{2,120})"',
    re.IGNORECASE,
)

_MMK_STRING_KEY_RE = re.compile(
    r"(?i)^(?:"
    r"is_?premium|premium|premium_?status|is_?vip|vip|svip|"
    r"is_?pro|pro_user|pro_version|is_?subscribed|subscription|"
    r"sub_?status|is_?purchased|purchased|is_?paid|unlocked|"
    r"no_?ads|ad_?free|remove_?ads|lifetime|entitlement|"
    r"has_premium|has_vip|has_pro|billing|sku"
    r")$"
)

_MMK_PREMIUM_FIELD_RE = re.compile(
    r"(?i)([is]get-boolean|[is]put-boolean)\s+[vp]\d+.*;->"
    r"(?P<field>(?:is|has|get|set)?[A-Za-z0-9_]*(?:Premium|Vip|SVIP|ProUser|ProVersion|"
    r"Subscri|Purchased|Paid|Unlocked|NoAds|AdFree|LifeTime|Elite)[A-Za-z0-9_]*):Z"
)

_MMK_PREFS_GET_RE = re.compile(
    r"invoke-.*SharedPreferences;->get(Boolean|Int|Long|String)\("
)
_MMK_BILLING_SDK_RE = re.compile(
    r"(?i)L(?:com/android/billingclient/|com/android/vending/billing/|"
    r"com/revenuecat/|com/android/billing/|"
    r"com/pairip/licensecheck/|"
    r"[^;]*(?:BillingClient|Purchase|SkuDetails|CustomerInfo|Entitlement)[^;]*)"
)

_MMK_METHOD_SIG_RE = re.compile(
    r"^\.method\s+(?P<access>[\w\s]+?)\s+(?P<name>[\w$<>]+)\((?P<params>[^)]*)\)(?P<ret>\S+)"
)
_MMK_CLASS_RE = re.compile(r"^\.class\s+.*?(?P<cls>L[^;]+;)", re.MULTILINE)

_MMK_PKG_HINT_RE = re.compile(
    r"(?i)(?:billing|purchase|premium|subscription|vip|iap|inapp|license)"
)


def _mmk_smali_to_java(cls):
    if not cls:
        return "-"
    c = cls.strip()
    if c.startswith("L") and c.endswith(";"):
        c = c[1:-1]
    return c.replace("/", ".")


def _mmk_extract_class(content):
    m = _MMK_CLASS_RE.search(content)
    return _mmk_smali_to_java(m.group("cls")) if m else "-"


def _mmk_method_at_line(lines, line_no):
    current = "-"
    for i, ln in enumerate(lines, 1):
        if i > line_no:
            break
        s = ln.strip()
        if s.startswith(".method"):
            m = _MMK_METHOD_SIG_RE.match(s)
            if m:
                current = "%s(%s)%s" % (m.group("name"), m.group("params"), m.group("ret"))
        elif s.startswith(".end method"):
            current = "-"
    return current


def _mmk_ctx(lines, line_no, radius=3):
    start = max(0, line_no - 1 - radius)
    end = min(len(lines), line_no + radius)
    out = []
    for idx in range(start, end):
        mark = ">>" if idx == line_no - 1 else "  "
        out.append("%s %d: %s" % (mark, idx + 1, lines[idx].rstrip()[:120]))
    return "\n".join(out)


def _mmk_is_false_positive(text):
    if not text:
        return True
    if _MMK_PREMIUM_FALSE.search(text):
        # masih boleh jika ada strong token premium/vip di sampingnya
        if _MMK_PREMIUM_STRONG_RE.search(text):
            return False
        return True
    return False


def _mmk_score_hit(match_type, keyword, class_name, line_text, nearby=""):
    """Skor 0–100 untuk ranking (bukan kepastian)."""
    score = 40
    kw = (keyword or "").lower()
    blob = " ".join([keyword or "", class_name or "", line_text or "", nearby or ""]).lower()

    if match_type == "method_sig":
        score = 75
    elif match_type == "field":
        score = 80
    elif match_type == "string_key":
        score = 88
    elif match_type == "prefs":
        score = 90
    elif match_type == "sdk":
        score = 70
    elif match_type == "string":
        score = 65
    elif match_type == "name":
        score = 55

    if _MMK_PREMIUM_STRONG_RE.search(kw) or _MMK_PREMIUM_STRONG_RE.search(blob):
        score += 15
    if _MMK_PKG_HINT_RE.search(class_name or ""):
        score += 10
    if "billing" in blob or "purchase" in blob or "subscription" in blob:
        score += 8
    if re.search(r"\b[a-z]{1,2}\(\)Z$", (keyword or "")):
        score -= 20  # method obf sangat pendek tanpa bukti lain
    if _mmk_is_false_positive(blob) and match_type not in ("prefs", "string_key", "field"):
        score -= 35
    return max(0, min(100, score))


def _mmk_scan_smali_file(fp, root):
    hits = []
    try:
        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except Exception:
        return hits
    try:
        rel = os.path.relpath(fp, root)
    except Exception:
        rel = fp
    cls = _mmk_extract_class(text)
    lines = text.splitlines()
    pkg_boost = bool(_MMK_PKG_HINT_RE.search(cls)) or bool(_MMK_PKG_HINT_RE.search(rel))

    # Pre-index const-string lines for prefs window
    string_lines = {}  # line_no -> string value
    for i, line in enumerate(lines, 1):
        m = _MMK_PREMIUM_STRING_RE.search(line)
        if m:
            string_lines[i] = m.group("s")

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("."):
            # method signatures still start with .method
            pass

        # 1) method signature — strong/med names only
        if stripped.startswith(".method"):
            m = _MMK_METHOD_SIG_RE.match(stripped)
            if m:
                name = m.group("name")
                if _mmk_is_false_positive(name):
                    continue
                if _MMK_PREMIUM_STRONG_RE.search(name) or (
                    _MMK_PREMIUM_MED_RE.search(name) and (pkg_boost or len(name) > 8)
                ):
                    meth = "%s(%s)%s" % (name, m.group("params"), m.group("ret"))
                    hits.append({
                        "file": rel, "class_name": cls, "method": meth,
                        "line_no": i, "line_text": stripped[:200],
                        "match_type": "method_sig", "keyword": name,
                        "context": _mmk_ctx(lines, i),
                        "score": _mmk_score_hit("method_sig", name, cls, stripped),
                    })
            continue

        if not stripped or stripped.startswith("#"):
            continue

        # 2) exact-ish preference keys in const-string
        m = _MMK_PREMIUM_STRING_RE.search(stripped)
        if m:
            s = m.group("s")
            if _MMK_STRING_KEY_RE.match(s.strip()) or _MMK_PREMIUM_STRONG_RE.search(s):
                if not _mmk_is_false_positive(s) or _MMK_PREMIUM_STRONG_RE.search(s):
                    # lihat 8 baris ke bawah: ada getBoolean?
                    window = "\n".join(lines[i - 1:min(len(lines), i + 10)])
                    mtype = "prefs" if _MMK_PREFS_GET_RE.search(window) else "string_key"
                    hits.append({
                        "file": rel, "class_name": cls,
                        "method": _mmk_method_at_line(lines, i),
                        "line_no": i, "line_text": stripped[:200],
                        "match_type": mtype, "keyword": s[:80],
                        "context": _mmk_ctx(lines, i),
                        "score": _mmk_score_hit(mtype, s, cls, stripped, window),
                    })
                    continue
            elif _MMK_PREMIUM_MED_RE.search(s) and not _mmk_is_false_positive(s):
                window = "\n".join(lines[i - 1:min(len(lines), i + 10)])
                if _MMK_PREFS_GET_RE.search(window) or pkg_boost:
                    hits.append({
                        "file": rel, "class_name": cls,
                        "method": _mmk_method_at_line(lines, i),
                        "line_no": i, "line_text": stripped[:200],
                        "match_type": "string", "keyword": s[:80],
                        "context": _mmk_ctx(lines, i),
                        "score": _mmk_score_hit("string", s, cls, stripped, window),
                    })
                    continue

        # 3) field boolean premium*
        m = _MMK_PREMIUM_FIELD_RE.search(stripped)
        if m:
            field = m.group("field")
            if not _mmk_is_false_positive(field):
                hits.append({
                    "file": rel, "class_name": cls,
                    "method": _mmk_method_at_line(lines, i),
                    "line_no": i, "line_text": stripped[:200],
                    "match_type": "field", "keyword": field,
                    "context": _mmk_ctx(lines, i),
                    "score": _mmk_score_hit("field", field, cls, stripped),
                })
                continue

        # 4) billing SDK type refs
        if _MMK_BILLING_SDK_RE.search(stripped):
            hits.append({
                "file": rel, "class_name": cls,
                "method": _mmk_method_at_line(lines, i),
                "line_no": i, "line_text": stripped[:200],
                "match_type": "sdk", "keyword": "billing_sdk",
                "context": _mmk_ctx(lines, i),
                "score": _mmk_score_hit("sdk", "billing_sdk", cls, stripped),
            })
            continue

        # 5) prefs getBoolean preceded by suspicious string (window up)
        if _MMK_PREFS_GET_RE.search(stripped):
            prev = "\n".join(lines[max(0, i - 12):i])
            sm = re.findall(r'const-string(?:/jumbo)?\s+[vp]\d+\s*,\s*"([^"]+)"', prev, re.I)
            for s in sm:
                if _MMK_STRING_KEY_RE.match(s.strip()) or _MMK_PREMIUM_STRONG_RE.search(s):
                    hits.append({
                        "file": rel, "class_name": cls,
                        "method": _mmk_method_at_line(lines, i),
                        "line_no": i, "line_text": stripped[:200],
                        "match_type": "prefs", "keyword": s[:80],
                        "context": _mmk_ctx(lines, i),
                        "score": _mmk_score_hit("prefs", s, cls, stripped, prev),
                    })
                    break

    return hits


def _mmk_scan_smali_tree(root, min_score=50):
    all_hits = []
    n = 0
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".smali"):
                continue
            n += 1
            fp = os.path.join(dirpath, fn)
            all_hits.extend(_mmk_scan_smali_file(fp, root))
            if n % 300 == 0:
                progress_live(min(95.0, n / 50.0), "smali %d" % n)
    if n:
        progress_live(100.0, "done")
        print()
    # filter + sort by score
    filtered = [h for h in all_hits if int(h.get("score") or 0) >= min_score]
    filtered.sort(key=lambda h: (-int(h.get("score") or 0), h.get("file") or "", h.get("line_no") or 0))
    return filtered, n, len(all_hits)


def _mmk_premium_save_report(hits, scanned, src, out_dir, raw_count=0):
    import json as _json
    from datetime import datetime
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception:
        out_dir = os.getcwd()
    data = {
        "input_path": src,
        "scanned_files": scanned,
        "hit_count": len(hits),
        "raw_hit_count": raw_count,
        "notes": "Defensive analysis only — no modification. Ranked by confidence score.",
        "hits": hits,
    }
    jp = os.path.join(out_dir, "premium_scan_%s.json" % stamp)
    tp = os.path.join(out_dir, "premium_scan_%s.txt" % stamp)
    with open(jp, "w", encoding="utf-8") as f:
        _json.dump(data, f, indent=2, ensure_ascii=False)
    with open(tp, "w", encoding="utf-8") as f:
        f.write("DEFENSIVE PREMIUM-LOGIC SCAN REPORT\n")
        f.write("No modification — identification only\n")
        f.write("Input: %s\nSmali: %d\nHits(score>=50): %d\nRaw: %d\n\n" % (
            src, scanned, len(hits), raw_count))
        for i, h in enumerate(hits, 1):
            f.write("[%d] score=%s %s · %s\n" % (i, h.get("score"), h.get("match_type"), h.get("keyword")))
            f.write("    Method: %s\n" % h.get("method"))
            f.write("    Class : %s\n" % h.get("class_name"))
            f.write("    File  : %s:%s\n" % (h.get("file"), h.get("line_no")))
            f.write("    Line  : %s\n\n" % h.get("line_text"))
    return jp, tp


def _mmk_premium_print_results(hits, limit_table=60, limit_box=15):
    if not hits:
        print("  (tidak ada kandidat dengan skor cukup)")
        return
    print()
    print("  ┌──────┬──────┬──────────────────────┬────────────────────────┬──────────┬────────────┐")
    print("  │  NO  │ SCORE│ METHOD               │ CLASS                  │ TYPE     │ KEYWORD    │")
    print("  ├──────┼──────┼──────────────────────┼────────────────────────┼──────────┼────────────┤")
    for i, h in enumerate(hits[:limit_table], 1):
        meth = (h.get("method") or "-")[:20]
        cls = (h.get("class_name") or "-")[:22]
        typ = (h.get("match_type") or "-")[:8]
        kw = (h.get("keyword") or "-")[:10]
        sc = int(h.get("score") or 0)
        print("  │ %4d │ %4d │ %-20s │ %-22s │ %-8s │ %-10s │" % (i, sc, meth, cls, typ, kw))
    print("  └──────┴──────┴──────────────────────┴────────────────────────┴──────────┴────────────┘")
    if len(hits) > limit_table:
        print("  … +%d hit (lihat laporan JSON/TXT)" % (len(hits) - limit_table))
    for i, h in enumerate(hits[:limit_box], 1):
        print()
        print("  ╔══════════════════════════════════════════════════════════╗")
        print("  ║  HIT #%-4d · %-10s · score %-3s                    ║" % (
            i, (h.get("match_type") or "")[:10], str(h.get("score"))))
        print("  ╠══════════════════════════════════════════════════════════╣")
        print("  ║  Method   : %-44s ║" % ((h.get("method") or "-")[:44]))
        print("  ║  Class    : %-44s ║" % ((h.get("class_name") or "-")[:44]))
        print("  ║  Keyword  : %-44s ║" % ((h.get("keyword") or "-")[:44]))
        print("  ║  File     : %-44s ║" % ((h.get("file") or "-")[:44]))
        print("  ║  Line     : %-44s ║" % (str(h.get("line_no"))))
        print("  ║  Code     : %-44s ║" % ((h.get("line_text") or "-")[:44]))
        print("  ╚══════════════════════════════════════════════════════════╝")


def premium_logic_scan_main():
    """
    Opsi 22 — Defensive Premium Logic Scan (identifikasi saja, TANPA patch).
    Logic scanner tertanam di script utama (tidak butuh tool.py terpisah).
    """
    banner("PREMIUM LOGIC SCAN", "defensive · identify only · no patch")
    info("Hanya laporan kandidat logic premium/VIP/subscription")
    warn("Tidak memodifikasi APK / smali")
    print()

    mmk_ensure_dirs()
    out_dir = MMK_OUT_APP if "MMK_OUT_APP" in globals() else os.path.join(os.getcwd(), "premium_scan_out")
    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception:
        out_dir = os.getcwd()

    print("  %s%s▶ SUMBER%s" % (C.BOLD, C.CYAN, C.RESET))
    print("     %s1)%s  APK/APKS dari menu/app  %s(auto-decompile read-only)%s" % (C.GREEN, C.RESET, C.DIM, C.RESET))
    print("     %s2)%s  Folder decompile (.smali)" % (C.GREEN, C.RESET))
    print("     %s0)%s  Back" % (C.RED, C.RESET))
    mode = input("  %sPilih ➤%s " % (C.MAGENTA, C.RESET)).strip() or "1"
    if mode in ("0", "q"):
        return

    scan_path = None
    temp_dec = None
    src_label = ""

    try:
        if mode == "2":
            raw = input("  %sPath folder decompile ➤%s " % (C.CYAN, C.RESET)).strip()
            if not raw or not os.path.isdir(raw):
                err("Folder tidak valid")
                return
            scan_path = os.path.abspath(raw)
            src_label = scan_path
        else:
            entries = mmk_list_apks((".apk", ".apks", ".xapk"))
            if not entries:
                err("Tidak ada APK di %s" % MMK_APP_DIR)
                info("Atau pilih mode 2 + folder .smali")
                return
            chosen = select_target(entries, title="SELECT APK  ·  PREMIUM SCAN") if "select_target" in globals() else entries[0][0]
            if not chosen:
                return
            apk_path = os.path.abspath(chosen)
            src_label = apk_path
            ok("Target: %s" % os.path.basename(apk_path))

            jar = None
            for finder in ("_smali_ensure_apkeditor", "_smali_find_apkeditor", "find_apkeditor_jar"):
                if finder in globals():
                    try:
                        jar = globals()[finder]()
                    except Exception:
                        jar = None
                    if jar:
                        break
            if not jar or not shutil.which("java"):
                err("Scan dari APK butuh Java + APKEditor.jar (decompile baca-saja)")
                info("Atau decompile manual → mode 2")
                return

            base = os.path.splitext(os.path.basename(apk_path))[0]
            temp_dec = os.path.abspath("_scan_dec_%s" % base)
            if os.path.isdir(temp_dec):
                shutil.rmtree(temp_dec, ignore_errors=True)
            if apk_path.lower().endswith((".apks", ".xapk")):
                merged = os.path.splitext(apk_path)[0] + "_scan_merged.apk"
                run_java_quiet(["java", "-jar", os.path.abspath(jar), "m", "-i", apk_path, "-o", merged, "-f"], label="MERGE")
                if os.path.isfile(merged):
                    apk_path = merged
            banner("DECOMPILE (read-only)", "untuk scan smali")
            rc = run_java_quiet(
                ["java", "-jar", os.path.abspath(jar), "d", "-i", apk_path, "-o", temp_dec, "-f"],
                label="DECOMPILE",
            )
            if rc != 0 or not os.path.isdir(temp_dec):
                err("Decompile gagal — tidak bisa scan")
                return
            scan_path = temp_dec

        banner("SCAN", "premium / vip / subscription keywords")
        hits, nfiles, raw_n = _mmk_scan_smali_tree(scan_path, min_score=50)
        if nfiles == 0:
            warn("Tidak ada file .smali di path scan")
            info("Pastikan folder decompile atau APK berhasil di-decompile")

        # dedup
        seen = set()
        unique = []
        for h in hits:
            key = (h.get("file"), h.get("line_no"), h.get("match_type"), h.get("keyword"))
            if key in seen:
                continue
            seen.add(key)
            unique.append(h)

        jp, tp = _mmk_premium_save_report(unique, nfiles, src_label, out_dir, raw_count=raw_n)
        _mmk_premium_print_results(unique)

        print()
        print("  %s╔%s╗%s" % (C.MAGENTA, "═" * 58, C.RESET))
        print("  %s║%s%s%s%s║%s" % (C.MAGENTA, C.RESET, C.BOLD, C.GREEN, "PREMIUM SCAN DONE — MMK MOD".center(58), C.RESET + C.MAGENTA))
        print("  %s╠%s╣%s" % (C.MAGENTA, "═" * 58, C.RESET))
        print("  %s║%s  Hits     : %d" % (C.MAGENTA, C.RESET, len(unique)))
        print("  %s║%s  Smali    : %d" % (C.MAGENTA, C.RESET, nfiles))
        print("  %s║%s  JSON     : %s" % (C.MAGENTA, C.RESET, os.path.basename(jp)))
        print("  %s║%s  TXT      : %s" % (C.MAGENTA, C.RESET, os.path.basename(tp)))
        print("  %s║%s  Direktori: %s" % (C.MAGENTA, C.RESET, out_dir[:48]))
        print("  %s║%s  Mode     : identify-only (no patch)" % (C.MAGENTA, C.RESET))
        print("  %s╚%s╝%s" % (C.MAGENTA, "═" * 58, C.RESET))
        try:
            if "mmk_history_add" in globals():
                mmk_history_add("premium_scan", None, extra={"ok": 1, "steps": "hits=%d" % len(unique)})
        except Exception:
            pass
    except Exception as e:
        err("Scan error: %s" % e)
        import traceback
        traceback.print_exc()
    finally:
        if temp_dec and os.path.isdir(temp_dec):
            try:
                shutil.rmtree(temp_dec, ignore_errors=True)
            except Exception:
                pass



def unprotect_apk_main():
    """
    Buka / kurangi proteksi APK — level low → high.
    Tidak menjamin buka packer native (DPT/CyberArmor shell penuh).
    """
    banner("BUKA PROTEKSI", "unpack · clean · level 1–5")
    info("Level tinggi = lebih agresif, risiko app rusak naik")
    print()
    # tabel level dalam box
    print(f"  {C.CYAN}┌────┬────────┬──────────────────────────────────────────┐{C.RESET}")
    print(f"  {C.CYAN}│{C.RESET}{C.YELLOW} LV {C.RESET}{C.CYAN}│{C.RESET}{C.YELLOW} NAMA   {C.RESET}{C.CYAN}│{C.RESET}{C.YELLOW} KETERANGAN                             {C.RESET}{C.CYAN}│{C.RESET}")
    print(f"  {C.CYAN}├────┼────────┼──────────────────────────────────────────┤{C.RESET}")
    _lv_rows = [
        ("1", "LOW",  "Decompile + rebuild (bersih resource)"),
        ("2", "LOW+", "LOW + hapus NOP berlebih di smali"),
        ("3", "MID",  "LOW+ + normalisasi smali ringan"),
        ("4", "HIGH", "MID + strip .line/.local debug"),
        ("5", "MAX",  "HIGH + rezip dex/res agresif"),
        ("0", "EXIT", "Kembali ke menu"),
    ]
    for a, b, c in _lv_rows:
        col = C.GREEN if a != "0" else C.RED
        print(f"  {C.CYAN}│{C.RESET}{col} {a:^2} {C.RESET}{C.CYAN}│{C.RESET} {b:<6} {C.CYAN}│{C.RESET} {c:<40} {C.CYAN}│{C.RESET}")
    print(f"  {C.CYAN}└────┴────────┴──────────────────────────────────────────┘{C.RESET}")
    lv = input(f"  {C.MAGENTA}Level [1-5] ➤{C.RESET} ").strip()
    if lv in ("0", "", "q"):
        return
    if not lv.isdigit() or not (1 <= int(lv) <= 5):
        err("Level tidak valid")
        return
    level = int(lv)

    entries = mmk_list_apks((".apk", ".apks", ".xapk"))
    if not entries:
        err(f"Tidak ada APK di {MMK_APP_DIR}")
        return
    apk_path = select_target(entries, title="SELECT APK  ·  BUKA PROTEKSI") if "select_target" in globals() else entries[0][0]
    if not apk_path:
        return
    ok(f"Target: {os.path.basename(apk_path)}")

    jar = None
    try:
        jar = _find_or_fetch_apkeditor() if "_find_or_fetch_apkeditor" in globals() else None
    except Exception:
        pass
    if not jar:
        try:
            jar = _smali_ensure_apkeditor()
        except Exception:
            pass
    if not jar:
        err("APKEditor.jar diperlukan")
        info(f"Letakan di: {MMK_FILES_DIR}")
        return
    jar = os.path.abspath(jar)

    # merge apks
    if apk_path.lower().endswith((".apks", ".xapk")):
        merged = os.path.splitext(apk_path)[0] + "_merged.apk"
        run_java_quiet(["java", "-jar", jar, "m", "-i", apk_path, "-o", merged, "-f"], label="MERGE")
        if os.path.isfile(merged):
            apk_path = merged
            ok(f"Merged: {os.path.basename(apk_path)}")
        else:
            err("Merge gagal")
            return

    base = os.path.splitext(os.path.basename(apk_path))[0]
    dec = os.path.abspath(f"_unprotect_{base}_dec")
    work_out = os.path.abspath(f"{base}_unprotect_L{level}.apk")
    dest = mmk_output("app", f"{base}_unprotect_L{level}.apk")
    if os.path.isdir(dec):
        shutil.rmtree(dec, ignore_errors=True)
    for pth in (work_out, dest):
        if os.path.exists(pth):
            try:
                os.remove(pth)
            except Exception:
                pass

    # ── Level 1+: always decompile ──
    banner("DECOMPILE", f"level {level}")
    box_cmd_short("decompile", apk_path, dec, f"unprotect L{level}")
    rc = run_java_quiet(["java", "-jar", jar, "d", "-i", apk_path, "-o", dec, "-f"], label="DECOMPILE")
    if rc != 0 or not os.path.isdir(dec):
        err("Decompile gagal — proteksi terlalu kuat / corrupt")
        run_java_quiet_show_errors()
        return

    # ── Level 2+: strip excessive nop ──
    if level >= 2:
        banner("CLEAN SMALI", "hapus NOP berlebih")
        n_files = 0
        n_nop = 0
        for root, _, fs in os.walk(dec):
            for fn in fs:
                if not fn.endswith(".smali"):
                    continue
                fp = os.path.join(root, fn)
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                except Exception:
                    continue
                out = []
                prev_nop = 0
                changed = False
                for ln in lines:
                    if ln.strip() == "nop":
                        prev_nop += 1
                        # level 2: keep max 1 consecutive; level 3+: remove all standalone nop chains >0
                        if level >= 3:
                            changed = True
                            n_nop += 1
                            continue
                        if prev_nop > 1:
                            changed = True
                            n_nop += 1
                            continue
                        out.append(ln)
                    else:
                        prev_nop = 0
                        out.append(ln)
                if changed:
                    try:
                        with open(fp, "w", encoding="utf-8") as f:
                            f.writelines(out)
                        n_files += 1
                    except Exception:
                        pass
        ok(f"NOP dibersihkan: {n_nop} di {n_files} file")

    # ── Level 3+: light string/smali normalize ──
    if level >= 3:
        banner("NORMALIZE", "rapikan smali ringan")
        # hapus baris kosong berlebih di method
        n = 0
        for root, _, fs in os.walk(dec):
            for fn in fs:
                if not fn.endswith(".smali"):
                    continue
                fp = os.path.join(root, fn)
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except Exception:
                    continue
                new = re.sub(r"\n{3,}", "\n\n", content)
                if new != content:
                    try:
                        with open(fp, "w", encoding="utf-8") as f:
                            f.write(new)
                        n += 1
                    except Exception:
                        pass
        ok(f"Normalized: {n} files")

    # ── Level 4+: strip debug info lines ──
    if level >= 4:
        banner("STRIP DEBUG", ".line / .local / .param verbose")
        n = 0
        for root, _, fs in os.walk(dec):
            for fn in fs:
                if not fn.endswith(".smali"):
                    continue
                fp = os.path.join(root, fn)
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                except Exception:
                    continue
                out = []
                changed = False
                for ln in lines:
                    s = ln.strip()
                    if s.startswith(".line ") or s.startswith(".local ") or s.startswith(".end local"):
                        changed = True
                        continue
                    out.append(ln)
                if changed:
                    try:
                        with open(fp, "w", encoding="utf-8") as f:
                            f.writelines(out)
                        n += 1
                    except Exception:
                        pass
        ok(f"Debug stripped: {n} files")

    # ── Level 5: extra zip repair attempt on original if decompile weak ──
    if level >= 5:
        banner("MAX", "rezip integrity check")
        info("Mencoba pastikan struktur APK valid setelah rebuild")

    banner("BUILD", f"unprotect L{level}")
    box_cmd_short("build", dec, work_out, f"unprotect L{level}")
    rc = run_java_quiet(["java", "-jar", jar, "b", "-i", dec, "-o", work_out, "-f"], label="BUILD")
    if not os.path.isfile(work_out):
        run_java_quiet(["java", "-jar", jar, "b", "-i", dec, "-o", work_out, "-f", "-dex-lib", "jf"], label="BUILD jf")
    shutil.rmtree(dec, ignore_errors=True)

    if not os.path.isfile(work_out) or os.path.getsize(work_out) < 1000:
        err("Build gagal — proteksi mungkin shell native (DPT/CyberArmor)")
        run_java_quiet_show_errors()
        info("Packer native tidak bisa dibuka hanya dengan decompile smali")
        return

    try:
        if os.path.abspath(work_out) != os.path.abspath(dest):
            shutil.move(work_out, dest)
        out = dest
    except Exception:
        out = work_out

    print()
    box_info([
        f"Level  : {level}",
        f"Output : {os.path.basename(out)}",
        f"Size   : {human_size(os.path.getsize(out))}",
        f"Direktori : {os.path.dirname(os.path.abspath(out))}",
        "Note   : Sign ulang jika install gagal (menu 6)",
    ], title="UNPROTECT DONE")
    ok(f"Selesai → {out}")
    # history optional
    try:
        if "mmk_history_add" in globals():
            mmk_history_add("unprotect", out, {"level": level})
    except Exception:
        pass


def protect_apk_main():
    """
    Protect APK — multi engine, prioritaskan yang tidak stuck splash.

    Mode:
      1 SAFE   = Resources only (APKEditor p)
      2 MILD   = APKEditor res + dex-level 1
      3 DPT SAFE / 4 DPT MAX
      5 Smali High
      6 CyberArmor — DEX encrypt + RASP (github.com/VexoraWebServices/CyberArmor)
    """
    banner("PROTECT APK", "MMK MOD  •  stabil dulu, baru high")
    info("Credit: MMK MOD")
    warn("Jika stuck di logo/splash → jangan pakai DPT MAX, coba mode 1 atau 3")
    print()

    if not shutil.which("java"):
        err("Java diperlukan")
        return

    menu_table([
        ("1", "SAFE", "Resources only · stabil"),
        ("2", "MILD", "Res + Dex level 0-5 (pilih)"),
        ("3", "DPT SAFE", "shell ringan -K"),
        ("4", "DPT MAX", "shell penuh (risiko splash)"),
        ("5", "Smali High", "goto/nop · no shell"),
        ("6", "CyberArmor", "native packer · NDK"),
        ("7", "Dalvik Obf", "thuxnder research NOP"),
        ("8", "ProGuard", "Guardsquare rename"),
        ("0", "Kembali", ""),
    ], headers=("NO", "MODE", "KETERANGAN"), width_cols=(4, 14, 32))
    print()
    preset = (globals().get("MMK_PRESET_OPTIONS") or {}).get("7")
    if preset in ("1", "2", "3", "4", "5", "6", "7", "8"):
        mode = preset
        ok(f"Mode preset (multibypass): {mode}")
    else:
        mode = input(f"  {C.MAGENTA}Pilih [1-8] default 1 (SAFE) ➤{C.RESET} ").strip() or "1"
        if mode not in ("1", "2", "3", "4", "5", "6", "7", "8"):
            mode = "1"

    entries = mmk_list_apks()
    if not entries:
        err(f"Tidak ada APK di {MMK_APP_DIR}")
        info(f"Letakkan APK di: {MMK_APP_DIR}")
        return
    apk_path = select_target(entries, title="SELECT TARGET  •  PROTECT") if "select_target" in globals() else os.path.abspath(apks[0])
    if not apk_path:
        return
    apk_path = os.path.abspath(apk_path)
    ok(f"Target: {os.path.basename(apk_path)}")

    jar_abs = _find_or_fetch_apkeditor()

    if apk_path.lower().endswith((".apks", ".xapk")):
        if not jar_abs:
            err("Butuh APKEditor untuk merge APKS")
            return
        merged = os.path.splitext(apk_path)[0] + "_merged.apk"
        run_java_quiet(["java", "-jar", jar_abs, "m", "-i", apk_path, "-o", merged, "-f"], label="MERGE")
        if not os.path.isfile(merged):
            run_java_quiet(["java", "-jar", jar_abs, "m", "-i", apk_path, "-o", merged, "-f"], label="MERGE")
        if not os.path.isfile(merged):
            err("Merge gagal")
            return
        apk_path = os.path.abspath(merged)
        ok(f"Merged: {os.path.basename(apk_path)}")

    t0 = time.time()
    out_apk = None
    engine = ""

    # ── 1 SAFE: resources only ──
    if mode == "1":
        if not jar_abs:
            err("Butuh APKEditor.jar")
            return
        base_stem = os.path.splitext(os.path.basename(apk_path))[0]
        out_name = base_stem + "_safe_protected.apk"
        dest = mmk_output("protect", out_name)
        work_out = os.path.abspath(out_name)
        for pth in (dest, work_out):
            if os.path.exists(pth):
                try:
                    os.remove(pth)
                except Exception:
                    pass
        banner("SAFE PROTECT", "APKEditor p — resources only")
        cmd = ["java", "-jar", jar_abs, "p", "-i", apk_path, "-o", work_out, "-f"]
        box_cmd_short("protect SAFE (resources)", apk_path, work_out, "dex-level: off")
        rc = run_java_quiet(cmd, label="SAFE PROTECT")
        found = None
        for c in (work_out, dest, os.path.splitext(apk_path)[0] + "_protected.apk"):
            if c and os.path.isfile(c) and os.path.getsize(c) > 1000:
                found = c
                break
        if found:
            try:
                if os.path.abspath(found) != os.path.abspath(dest):
                    shutil.move(found, dest)
                out_apk = dest
            except Exception:
                out_apk = found
        else:
            run_java_quiet_show_errors()
            out_apk = None
        engine = "APKEditor resources SAFE"

    # ── 2 MILD: res + dex-level (0-5, user pilih) ──
    elif mode == "2":
        if not jar_abs:
            err("Butuh APKEditor.jar")
            return
        print()
        menu_table([
            ("0", "Off", "resource only (sama SAFE)"),
            ("1", "Basic", "stabil · rekomendasi ★"),
            ("2", "Normal", "coba; fallback ke 1 jika gagal"),
            ("3", "High", "coba; fallback otomatis"),
            ("4", "Max-", "coba; fallback otomatis"),
            ("5", "Max", "coba; fallback otomatis"),
        ], headers=("LV", "NAMA", "KETERANGAN"), width_cols=(4, 10, 36))
        info("Docs APKEditor: level 2–5 mungkin belum full di jar lama")
        lv_raw = input(f"  {C.MAGENTA}Dex level [0-5] default 1 ➤{C.RESET} ").strip()
        if not lv_raw:
            dex_level = 1
        elif lv_raw.isdigit() and 0 <= int(lv_raw) <= 5:
            dex_level = int(lv_raw)
        else:
            warn("Level tidak valid, pakai 1")
            dex_level = 1

        mmk_ensure_dirs()
        base_stem = os.path.splitext(os.path.basename(apk_path))[0]
        # tulis dulu ke cwd (paling aman di Termux), lalu pindah ke out/protect
        levels_try = [dex_level]
        for fb in (1, 0):
            if fb not in levels_try:
                levels_try.append(fb)

        out_apk = None
        used_level = dex_level
        for lv in levels_try:
            out_name = f"{base_stem}_mild_L{lv}_protected.apk"
            # path di out/protect
            dest = mmk_output("protect", out_name)
            # path kerja di cwd (hindari permission /storage)
            work_out = os.path.abspath(out_name)
            for pth in (dest, work_out):
                if os.path.exists(pth):
                    try:
                        os.remove(pth)
                    except Exception:
                        pass

            banner("MILD PROTECT", f"APKEditor p -dex-level {lv}")
            cmd = ["java", "-jar", jar_abs, "p", "-i", apk_path, "-o", work_out, "-f"]
            if lv > 0:
                cmd.extend(["-dex-level", str(lv)])
            box_cmd_short("protect MILD", apk_path, work_out, f"dex-level: {lv}")
            rc = run_java_quiet(cmd, label=f"MILD L{lv}")

            # APKEditor kadang simpan nama beda di folder input
            candidates = [work_out, dest]
            alt = os.path.splitext(apk_path)[0] + "_protected.apk"
            candidates.append(alt)
            candidates.append(os.path.join(os.path.dirname(apk_path), out_name))
            found = None
            for c in candidates:
                if c and os.path.isfile(c) and os.path.getsize(c) > 1000:
                    found = c
                    break
            if found:
                # pindahkan ke out/protect
                try:
                    if os.path.abspath(found) != os.path.abspath(dest):
                        shutil.move(found, dest)
                    out_apk = dest
                except Exception:
                    out_apk = found
                used_level = lv
                ok(f"Output: {os.path.basename(out_apk)} (dex-level {lv})")
                break
            else:
                warn(f"Level {lv} gagal (rc={rc}) — tidak ada file output")
                run_java_quiet_show_errors()
                if lv != levels_try[-1]:
                    warn(f"Coba level berikutnya...")

        engine = f"APKEditor res + dex-level {used_level}"
        if not out_apk or not os.path.isfile(out_apk):
            out_apk = None

    # ── 3/4 DPT ──
    elif mode in ("3", "4"):
        dpt = _find_dpt_jar()
        if not dpt:
            banner("DOWNLOAD", "dpt-shell dari GitHub")
            dpt = _download_dpt_shell(".")
        if not dpt:
            err("dpt-shell tidak tersedia")
            info("https://github.com/luoyesiqiu/dpt-shell/releases")
            return
        ok(f"dpt: {dpt}")
        safe = mode == "3"
        out_apk = _protect_dpt(apk_path, dpt, safe=safe)
        engine = "DPT-Shell SAFE" if safe else "DPT-Shell MAX"

    # ── 5 Smali High ──
    elif mode == "5":
        if not jar_abs:
            err("Butuh APKEditor.jar")
            return
        out_apk = _protect_smali_high(apk_path, jar_abs)
        engine = "Smali High"

    # ── 6 CyberArmor ──
    elif mode == "6":
        print()
        print(f"  {C.BOLD}Profile CyberArmor{C.RESET}")
        print(f"  {C.GREEN}1){C.RESET}  default  {C.DIM}(rekomendasi · anti-debug/frida/sign){C.RESET}")
        print(f"  {C.GREEN}2){C.RESET}  strict   {C.DIM}(+ root/emulator/ptrace){C.RESET}")
        print(f"  {C.GREEN}3){C.RESET}  none     {C.DIM}(pack only · debug launch){C.RESET}")
        psel = input(f"  {C.MAGENTA}Profile [1/2/3] default 1 ➤{C.RESET} ").strip() or "1"
        profile = {"1": "default", "2": "strict", "3": "none"}.get(psel, "default")
        out_apk = _protect_cyberarmor(apk_path, profile=profile)
        engine = f"CyberArmor ({profile})"

    # ── 7 Dalvik Obfuscator (research) ──
    elif mode == "7":
        if not jar_abs:
            err("Butuh APKEditor.jar (decompile/build)")
            return
        warn("RESEARCH ONLY — https://github.com/thuxnder/dalvik-obfuscator")
        ans = input(f"  {C.YELLOW}Lanjut? App bisa rusak [y/N] ➤{C.RESET} ").strip().lower()
        if ans not in ("y", "ya", "yes"):
            info("Dibatalkan")
            return
        out_apk = _protect_dalvik_obfuscator(apk_path, jar_abs)
        engine = "Dalvik-obfuscator (NOP research)"

    # ── 8 ProGuard ──
    elif mode == "8":
        warn("ProGuard pada APK butuh keep-rules; hasil bisa perlu sign ulang")
        out_apk = _protect_proguard(apk_path)
        engine = "ProGuard (Guardsquare)"

    if not out_apk or not os.path.isfile(out_apk):
        err("Protect gagal — tidak ada output")
        return

    dt = time.time() - t0
    try:
        sz = human_size(os.path.getsize(out_apk))
    except Exception:
        sz = "-"

    out_dir = os.path.dirname(os.path.abspath(out_apk)) or os.getcwd()
    print()
    print(f"  {C.MAGENTA}╔{'═'*58}╗{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}{C.BOLD}{C.GREEN}{'PROTECT DONE — MMK MOD'.center(58)}{C.RESET}{C.MAGENTA}║{C.RESET}")
    print(f"  {C.MAGENTA}╠{'═'*58}╣{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  Engine    : {C.CYAN}{engine[:42]}{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  Output    : {C.CYAN}{os.path.basename(out_apk)}{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  Size      : {sz}")
    print(f"  {C.MAGENTA}║{C.RESET}  Time      : {dt:.1f}s")
    print(f"  {C.MAGENTA}║{C.RESET}  Direktori : {C.CYAN}{out_dir[:44]}{C.RESET}")
    if len(out_dir) > 44:
        print(f"  {C.MAGENTA}║{C.RESET}              {C.DIM}{out_dir[44:88]}{C.RESET}")
    print(f"  {C.MAGENTA}╚{'═'*58}╝{C.RESET}")
    if mode == "6":
        info("CyberArmor sudah re-sign (jika --ks diberikan)")
        warn("Signing identity berubah — koordinasikan key dengan publisher")
    else:
        warn("Sign dulu (menu 6) dengan keystore yang SAMA seperti biasa")
    if mode in ("3", "4"):
        warn("Kalau masih stuck splash → coba mode 1 (SAFE) atau 2 (MILD)")



def _next_classes_dex_name(apk_path):
    """Jika ada classes5.dex → return classes6.dex; jika hanya classes.dex → classes2.dex"""
    nums = set()
    with zipfile.ZipFile(apk_path, "r") as z:
        for n in z.namelist():
            base = os.path.basename(n)
            if base == "classes.dex":
                nums.add(1)
            else:
                m = re.match(r"^classes(\d+)\.dex$", base, re.I)
                if m:
                    nums.add(int(m.group(1)))
    if not nums:
        return "classes.dex"
    nxt = max(nums) + 1
    if nxt == 1:
        return "classes.dex"
    return f"classes{nxt}.dex"


def run_sign_apk_interactive():
    """Sign APK dengan .jks / .keystore di direktori (jarsigner / apksigner)."""
    banner("SIGN APK", "MMK MOD  •  .jks / .keystore")
    info("Mencari keystore di folder kerja...")

    keys = _list_files_ext(".jks", ".keystore", ".key")
    # .key sering bukan java keystore — tetap tampilkan jks/keystore dulu
    keys = [e for e in keys if e[1].lower().endswith((".jks", ".keystore"))] + \
           [e for e in keys if e[1].lower().endswith(".key")]
    if not keys:
        warn("Tidak ada .jks/.keystore — buat debug.jks otomatis?")
        ans = input(f"  {C.CYAN}Buat debug.jks? [Y/n]{C.RESET} ➤ ").strip().lower()
        if ans in ("n", "no", "tidak"):
            info("Sesi dihentikan")
            input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
            return
        if not shutil.which("keytool"):
            err("keytool tidak ada (pkg install openjdk-17)")
            input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
            return
        key_path = os.path.abspath("debug.jks")
        spinner("keytool -genkeypair debug.jks...", 1.0)
        rc = subprocess.call([
            "keytool", "-genkeypair", "-v",
            "-keystore", key_path,
            "-alias", "androiddebugkey",
            "-keyalg", "RSA", "-keysize", "2048",
            "-validity", "10000",
            "-storepass", "android",
            "-keypass", "android",
            "-dname", "CN=MMK MOD, OU=MMK, O=MMK MOD, L=ID, ST=ID, C=ID",
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if rc != 0 or not os.path.exists(key_path):
            err("Gagal buat debug.jks")
            input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
            return
        ok("debug.jks dibuat (alias=androiddebugkey, pass=android)")
        keys = [(key_path, "debug.jks", os.path.getsize(key_path))]

    key_path = _pick_from_entries(keys, "SELECT KEYSTORE  •  .jks/.keystore")
    if not key_path:
        info("Dibatalkan")
        return
    ok(f"Keystore: {os.path.basename(key_path)}")

    entries = mmk_list_apks((".apk",))
    if not entries:
        err(f"Tidak ada APK untuk di-sign di {MMK_APP_DIR}")
        input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
        return
    apk_path = _pick_from_entries(entries, "SELECT APK  •  TO SIGN")
    if not apk_path:
        info("Dibatalkan")
        return
    ok(f"APK: {os.path.basename(apk_path)}")

    print()
    alias = input(f"  {C.CYAN}Key alias{C.RESET} [{C.DIM}key0{C.RESET}] ➤ ").strip() or "key0"
    storepass = input(f"  {C.CYAN}Store password{C.RESET} [{C.DIM}android{C.RESET}] ➤ ").strip() or "android"
    keypass = input(f"  {C.CYAN}Key password{C.RESET} [{C.DIM}sama store{C.RESET}] ➤ ").strip() or storepass

    stem = Path(apk_path).stem
    out_apk = f"{stem}-signed.apk"
    print()
    out_custom = input(f"  {C.CYAN}Output{C.RESET} [{C.DIM}{out_apk}{C.RESET}] ➤ ").strip()
    if out_custom:
        out_apk = out_custom if out_custom.endswith(".apk") else out_custom + ".apk"

    # zipalign optional
    aligned = f"{stem}-aligned.apk"
    zipalign = shutil.which("zipalign")
    if zipalign:
        spinner("zipalign...", 0.8)
        subprocess.call([zipalign, "-f", "-p", "4", apk_path, aligned],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(aligned):
            sign_input = aligned
            ok("zipalign OK")
        else:
            sign_input = apk_path
            warn("zipalign gagal — pakai APK asli")
    else:
        sign_input = apk_path
        info("zipalign tidak ada — skip")

    apksigner = shutil.which("apksigner")
    jarsigner = shutil.which("jarsigner")

    banner("SIGNING", os.path.basename(out_apk))
    ok_sign = False

    if apksigner:
        spinner("apksigner sign...", 1.2)
        cmd = [
            apksigner, "sign",
            "--ks", key_path,
            "--ks-key-alias", alias,
            "--ks-pass", f"pass:{storepass}",
            "--key-pass", f"pass:{keypass}",
            "--out", out_apk,
            sign_input,
        ]
        rc = subprocess.call(cmd)
        ok_sign = rc == 0 and os.path.exists(out_apk)
    elif jarsigner:
        spinner("jarsigner...", 1.2)
        # jarsigner signs in-place → copy first
        shutil.copy2(sign_input, out_apk)
        cmd = [
            jarsigner,
            "-keystore", key_path,
            "-storepass", storepass,
            "-keypass", keypass,
            "-sigalg", "SHA256withRSA",
            "-digestalg", "SHA-256",
            out_apk,
            alias,
        ]
        rc = subprocess.call(cmd)
        ok_sign = rc == 0 and os.path.exists(out_apk)
    else:
        err("apksigner / jarsigner tidak ditemukan")
        info("Termux: pkg install android-tools  atau  openjdk (jarsigner)")
        input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
        return

    # cleanup aligned temp
    if os.path.exists(aligned) and aligned != out_apk:
        try:
            os.remove(aligned)
        except Exception:
            pass

    if ok_sign:
        print()
        print(f"  {C.MAGENTA}╔{'═'*48}╗{C.RESET}")
        print(f"  {C.MAGENTA}║{C.RESET}{C.BOLD}{C.GREEN}{'SIGNED — MMK MOD'.center(48)}{C.RESET}{C.MAGENTA}║{C.RESET}")
        print(f"  {C.MAGENTA}║{C.RESET}  Output: {C.CYAN}{out_apk}{C.RESET}")
        print(f"  {C.MAGENTA}║{C.RESET}  Size  : {human_size(os.path.getsize(out_apk))}")
        print(f"  {C.MAGENTA}╚{'═'*48}╝{C.RESET}")
    else:
        err("Sign gagal — cek alias / password keystore")
    input(f"\n{C.YELLOW}Press Enter...{C.RESET}")


def _inject_dex_into_apk(apk_path, dex_path, entry_name):
    """Tambah file dex ke APK sebagai entry_name (mis. classes6.dex)."""
    out_apk = f"{Path(apk_path).stem}-dexinjected.apk"
    tmp = out_apk + ".tmp"
    with zipfile.ZipFile(apk_path, "r") as zin, zipfile.ZipFile(tmp, "w") as zout:
        for item in zin.infolist():
            # skip if same name already
            if item.filename == entry_name or item.filename.endswith("/" + entry_name):
                continue
            zout.writestr(item, zin.read(item.filename))
        # write new dex
        with open(dex_path, "rb") as f:
            data = f.read()
        info = zipfile.ZipInfo(entry_name)
        info.compress_type = zipfile.ZIP_DEFLATED
        zout.writestr(info, data)
    os.replace(tmp, out_apk)
    return out_apk


def _inject_hook_into_smali(decompile_dir, hook_line, activity=None):
    """
    Cari method onCreate / onResume di smali (opsional filter Activity),
    sisipkan hook setelah header method.
    activity: com.example.MainActivity atau path smali
    """
    hook_line = hook_line.strip()
    if not hook_line.startswith(" "):
        hook_insn = "    " + hook_line
    else:
        hook_insn = hook_line

    method_re = re.compile(
        r'(\.method\s+[^\n]*(onCreate|onResume)\([^\)]*\)V\s*\n'
        r'(?:\s*\.(?:registers|locals)\s+\d+\s*\n)?'
        r'(?:\s*\.param[^\n]*\n)*)',
        re.IGNORECASE,
    )

    # target file filter
    target_suffix = None
    if activity:
        act = activity.strip().replace(".", "/")
        if act.startswith("L") and act.endswith(";"):
            act = act[1:-1]
        if not act.endswith(".smali"):
            act += ".smali"
        target_suffix = act

    changed = 0
    smali_roots = []
    for name in os.listdir(decompile_dir):
        p = os.path.join(decompile_dir, name)
        if os.path.isdir(p) and (name == "smali" or name.startswith("smali_")):
            smali_roots.append(p)
    if not smali_roots:
        smali_roots = [decompile_dir]

    files_hit = []
    for base in smali_roots:
        for root, _, files in os.walk(base):
            for fn in files:
                if not fn.endswith(".smali"):
                    continue
                fp = os.path.join(root, fn)
                if target_suffix:
                    norm = fp.replace("\\", "/")
                    if not (norm.endswith(target_suffix) or fn == os.path.basename(target_suffix)):
                        continue
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except Exception:
                    continue
                if "onCreate" not in content and "onResume" not in content:
                    continue

                def _inject(m, _hook=hook_insn):
                    block = m.group(0)
                    if "Zxdialogs" in block or _hook.strip() in block:
                        return block
                    return block + _hook + "\n"

                new_c, n = method_re.subn(_inject, content)
                if n and new_c != content:
                    try:
                        with open(fp, "w", encoding="utf-8") as f:
                            f.write(new_c)
                        changed += n
                        files_hit.append(os.path.relpath(fp, decompile_dir))
                    except Exception:
                        pass
    return changed, files_hit


def run_inject_dex_hook_interactive():
    """
    1) Pilih APK
    2) Pilih .dex → inject sebagai classes(N+1).dex
    3) Opsional: inject hook invoke-static ke onCreate/onResume
    """
    banner("INJECT DEX + HOOK", "MMK MOD  •  classesN.dex + onCreate")

    entries = mmk_list_apks((".apk",))
    if not entries:
        err(f"Tidak ada APK di {MMK_APP_DIR}")
        input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
        return
    apk_path = _pick_from_entries(entries, "SELECT APK  •  TARGET")
    if not apk_path:
        return
    ok(f"APK: {os.path.basename(apk_path)}")

    dexes = _list_files_ext(".dex")
    if not dexes:
        err("Tidak ada file .dex di folder")
        info("Letakkan classes.dex / hook.dex di direktori ini")
        input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
        return
    dex_path = _pick_from_entries(dexes, "SELECT DEX  •  TO INJECT")
    if not dex_path:
        return
    ok(f"DEX: {os.path.basename(dex_path)}")

    next_name = _next_classes_dex_name(apk_path)
    info(f"Akan disisipkan sebagai: {C.CYAN}{next_name}{C.RESET}")

    print()
    print(f"  {C.BOLD}{C.CYAN}▶ ACTIVITY{C.RESET}")
    print(f"  {C.DIM}Contoh: com.example.MainActivity{C.RESET}")
    activity = input(f"  {C.CYAN}Activity{C.RESET} ➤ ").strip()

    print()
    print(f"  {C.BOLD}{C.CYAN}▶ HOOK CODE{C.RESET}")
    print(f"  {C.DIM}Contoh:{C.RESET}")
    print(f"  {C.DIM}invoke-static {{p0}}, Lcom/zx/zendialogs/Zxdialogs;->show(Landroid/content/Context;)V{C.RESET}")
    default_hook = "invoke-static {p0}, Lcom/zx/zendialogs/Zxdialogs;->show(Landroid/content/Context;)V"
    hook = input(f"\n  {C.CYAN}Hook line{C.RESET} [{C.DIM}Enter = default{C.RESET}] ➤ ").strip()
    if not hook:
        hook = default_hook
        ok(f"Hook default: {hook[:60]}...")

    banner("INJECT DEX", f"{os.path.basename(dex_path)} → {next_name}")
    spinner("Menulis APK...", 1.0)
    try:
        out_apk = _inject_dex_into_apk(apk_path, dex_path, next_name)
        ok(f"DEX injected → {os.path.basename(out_apk)}")
    except Exception as e:
        err(f"Inject DEX gagal: {e}")
        input(f"\n{C.YELLOW}Press Enter...{C.RESET}")
        return

    if hook:
        jar = None
        for finder in ("_smali_ensure_apkeditor", "_smali_find_apkeditor", "find_apkeditor_jar"):
            if finder in globals():
                try:
                    jar = globals()[finder]()
                except Exception:
                    jar = None
                if jar:
                    break
        if not jar:
            # last try listdir
            for f in os.listdir("."):
                if f.lower().endswith(".jar") and "apkeditor" in f.lower():
                    jar = f
                    break
        if not jar:
            warn("APKEditor tidak ada — hook smali di-skip (DEX tetap ter-inject)")
        elif not shutil.which("java"):
            warn("Java tidak ada — hook smali di-skip")
        else:
            banner("INJECT HOOK", "onCreate / onResume")
            work = f"{Path(out_apk).stem}_hook_dec"
            if os.path.isdir(work):
                shutil.rmtree(work, ignore_errors=True)
            spinner("Decompile untuk sisip hook...", 1.5)
            rc = run_java_quiet(["java", "-jar", jar, "d", "-i", out_apk, "-o", work], label="DECOMPILE")
            if rc != 0 or not os.path.isdir(work):
                err("Decompile gagal — DEX sudah di APK, hook batal")
            else:
                n, hits = _inject_hook_into_smali(work, hook, activity=activity if activity else None)
                ok(f"Hook disisipkan di {n} method(s)")
                for h in hits[:12]:
                    print(f"  {C.GREEN}◆{C.RESET} {h}")
                if len(hits) > 12:
                    info(f"... +{len(hits)-12} file lain")
                final_out = f"{Path(apk_path).stem}-injected.apk"
                spinner("Rebuild APK...", 1.5)
                if os.path.exists(final_out):
                    try:
                        os.remove(final_out)
                    except Exception:
                        pass
                rc = run_java_quiet(["java", "-jar", jar, "b", "-i", work, "-o", final_out], label="BUILD")
                if rc == 0 and os.path.exists(final_out):
                    # replace intermediate
                    try:
                        if out_apk != final_out and os.path.exists(out_apk):
                            os.remove(out_apk)
                    except Exception:
                        pass
                    out_apk = final_out
                    ok(f"Rebuild OK → {os.path.basename(out_apk)}")
                else:
                    err("Rebuild gagal — pakai APK hasil inject DEX saja")
                # cleanup
                ans = input(f"  {C.YELLOW}Hapus folder decompile? [Y/n]{C.RESET} ➤ ").strip().lower()
                if ans not in ("n", "no", "tidak"):
                    shutil.rmtree(work, ignore_errors=True)

    print()
    print(f"  {C.MAGENTA}╔{'═'*50}╗{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}{C.BOLD}{C.GREEN}{'INJECT DONE — MMK MOD'.center(50)}{C.RESET}{C.MAGENTA}║{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  Output : {C.CYAN}{os.path.basename(out_apk)}{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  DEX as : {next_name}")
    print(f"  {C.MAGENTA}║{C.RESET}  Hook   : {'yes' if hook else 'no'}")
    print(f"  {C.MAGENTA}║{C.RESET}  Size   : {human_size(os.path.getsize(out_apk))}")
    print(f"  {C.MAGENTA}╚{'═'*50}╝{C.RESET}")
    info("Sign APK setelah inject (Toolkit → 9 Sign APK)")
    input(f"\n{C.YELLOW}Press Enter...{C.RESET}")



def toolkit_main():
    """Launch Nexus Cloud Toolkit (option 4)"""
    try:
        # ensure rich
        try:
            from rich.console import Console
        except ImportError:
            print("  Installing rich + requests...")
            os.system(f"{sys.executable} -m pip install rich requests -q")
        app = NexusCloudTerminal()
        app.nexus_main_menu()
    except KeyboardInterrupt:
        print("\n  Toolkit closed")
    except Exception as e:
        print(f"  Toolkit error: {e}")
        import traceback
        traceback.print_exc()


# ═══════════════════════════════════════════════════════════════
#  ENTRY
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
#  SECTION: SIGN APK + INJECT DIALOG  (MMK MOD)
# ═══════════════════════════════════════════════════════════════

def _pick_files_by_ext(exts, title):
    files = []
    for f in sorted(os.listdir('.')):
        low = f.lower()
        if any(low.endswith(e) for e in exts) and os.path.isfile(f):
            try:
                sz = os.path.getsize(f)
            except OSError:
                sz = 0
            files.append((os.path.abspath(f), f, sz))
    if not files:
        err(f"Tidak ada file {exts} di folder ini")
        return None
    if 'select_target' in globals():
        return select_target(files, title=title)
    for i, (_, name, sz) in enumerate(files, 1):
        print(f"  {C.GREEN}{i:2d}{C.RESET}  {name}  {C.CYAN}{human_size(sz)}{C.RESET}")
    try:
        idx = int(input(f"  {C.MAGENTA}➤{C.RESET} ").strip())
        return files[idx - 1][0]
    except Exception:
        return None


def _list_keystore_files():
    keys = []
    for f in sorted(os.listdir('.')):
        low = f.lower()
        if low.endswith(('.jks', '.keystore', '.key')) and os.path.isfile(f):
            keys.append(f)
    return keys


def _auto_keystore_creds(keystore):
    """
    Deteksi password + alias otomatis — tanpa input user.
    Coba pass umum + env MMK_KS_PASS / MMK_KEY_PASS.
    Return (storepass, keypass, alias) atau (None, None, None).
    """
    candidates = []
    env_sp = os.environ.get("MMK_KS_PASS", "").strip()
    env_kp = os.environ.get("MMK_KEY_PASS", "").strip()
    if env_sp:
        candidates.append(env_sp)
    candidates.extend([
        "android", "Android", "password", "Password", "123456",
        "changeit", "secret", "keystore", "mmk", "mod", "",
    ])
    # unique keep order
    seen = set()
    passes = []
    for p in candidates:
        if p not in seen:
            seen.add(p)
            passes.append(p)

    if not shutil.which("keytool"):
        # fallback defaults
        return (env_sp or "android", env_kp or env_sp or "android", "androiddebugkey")

    for sp in passes:
        try:
            cmd = ["keytool", "-list", "-keystore", keystore, "-storepass", sp]
            out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, timeout=25)
        except Exception:
            continue
        alias = None
        for line in out.splitlines():
            if "PrivateKeyEntry" in line or "SecretKeyEntry" in line:
                alias = line.split(",")[0].strip()
                break
        if not alias:
            # baris alias kadang "alias_name, ..."
            for line in out.splitlines():
                line = line.strip()
                if line and not line.startswith(("Keystore", "Your", "Warning", "*")) and "," in line:
                    alias = line.split(",")[0].strip()
                    break
        if not alias:
            alias = "androiddebugkey"
        kp = env_kp or sp
        return (sp, kp, alias)
    return (None, None, None)


def sign_apk_main():
    """
    Sign APK — pilih .apk + .jks/.key saja.
    Tidak perlu input password/alias (auto-detect).
    """
    banner("SIGN APK", "MMK MOD  •  auto .jks/.key  •  tanpa input sandi")
    info("Credit: MMK MOD")
    info("Cukup pilih APK + keystore — password/alias dideteksi otomatis")
    print()

    apk = _pick_files_by_ext(('.apk',), "SELECT APK  •  SIGN")
    if not apk:
        return
    ok(f"APK: {os.path.basename(apk)}")

    keys = _list_keystore_files()
    if not keys:
        err("Tidak ada .jks / .keystore / .key di folder ini")
        info("Letakkan file keystore di direktori kerja")
        return

    entries = [(os.path.abspath(k), k, os.path.getsize(k)) for k in keys]
    if 'select_target' in globals():
        keystore = select_target(entries, title="SELECT KEYSTORE  •  .jks / .key")
        if not keystore:
            return
    else:
        keystore = os.path.abspath(keys[0])
    ok(f"Keystore: {os.path.basename(keystore)}")

    spinner("Auto-detect password & alias...", 0.8)
    storepass, keypass, alias = _auto_keystore_creds(keystore)
    if not storepass:
        err("Gagal buka keystore — password tidak dikenali")
        info("Set env: export MMK_KS_PASS='sandi_keystore'")
        return
    ok(f"Alias: {alias}")
    ok("Password: (auto)")

    out_apk = os.path.splitext(apk)[0] + "-signed.apk"
    shutil.copy2(apk, out_apk)

    banner("SIGNING", os.path.basename(out_apk))
    signed = False

    apksigner = shutil.which('apksigner')
    if apksigner:
        spinner("apksigner sign...", 1.0)
        cmd = [
            apksigner, 'sign',
            '--ks', keystore,
            '--ks-pass', f'pass:{storepass}',
            '--key-pass', f'pass:{keypass}',
            '--ks-key-alias', alias,
            out_apk,
        ]
        rc = subprocess.call(cmd)
        if rc == 0:
            ok("Signed with apksigner")
            signed = True
        else:
            warn("apksigner gagal — coba jarsigner")

    if not signed and shutil.which('jarsigner'):
        spinner("jarsigner...", 1.0)
        cmd = [
            'jarsigner', '-sigalg', 'SHA256withRSA', '-digestalg', 'SHA-256',
            '-keystore', keystore,
            '-storepass', storepass,
            '-keypass', keypass,
            out_apk, alias,
        ]
        rc = subprocess.call(cmd)
        if rc == 0:
            ok("Signed with jarsigner")
            signed = True
            if shutil.which('zipalign'):
                aligned = out_apk + ".aligned"
                subprocess.call(['zipalign', '-f', '4', out_apk, aligned])
                if os.path.exists(aligned):
                    os.replace(aligned, out_apk)
                    ok("zipalign OK")

    if not signed:
        err("Sign gagal — cek keystore / set MMK_KS_PASS")
        try:
            os.remove(out_apk)
        except Exception:
            pass
        return

    print()
    print(f"  {C.MAGENTA}╔{'═'*48}╗{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}{C.BOLD}{C.GREEN}{'SIGN COMPLETE — MMK MOD'.center(48)}{C.RESET}{C.MAGENTA}║{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  Output: {C.CYAN}{os.path.basename(out_apk)}{C.RESET}")
    print(f"  {C.MAGENTA}╚{'═'*48}╝{C.RESET}")



def _activity_to_smali_path(activity: str) -> str:
    """com.example.MainActivity or Lcom/...; → com/example/MainActivity.smali"""
    a = activity.strip()
    if a.startswith('L') and a.endswith(';'):
        a = a[1:-1]
    a = a.replace('.', '/').replace('\\', '/')
    if a.endswith('.smali'):
        return a
    return a + '.smali'


def _inject_hook_into_smali(smali_path: str, hook_code: str) -> bool:
    """Inject hook after .registers/.locals in onCreate or onResume."""
    if not os.path.isfile(smali_path):
        return False
    with open(smali_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    hook = hook_code.strip()
    if not hook.endswith('\n'):
        hook += '\n'

    # Prefer onCreate, then onResume
    method_re = re.compile(
        r'(\.method\s+[^\n]*\s+(onCreate|onResume)\([^\)]*\)[^\n]*\n'
        r'(?:\s*\.(?:registers|locals)\s+\d+\s*\n))',
        re.IGNORECASE,
    )

    def _repl(m):
        block = m.group(1)
        # avoid double inject
        if hook.strip() in content:
            return block
        return block + '    ' + hook.lstrip() + '\n'

    new_content, n = method_re.subn(_repl, content, count=1)
    if n == 0:
        # try broader: any onCreate method body start
        method_re2 = re.compile(
            r'(\.method\s+[^\n]*onCreate\([^\)]*\)V\s*\n\s*\.(?:registers|locals)\s+\d+\s*\n)',
            re.IGNORECASE,
        )
        new_content, n = method_re2.subn(_repl, content, count=1)

    if n == 0:
        return False
    if new_content == content:
        # already injected?
        if hook.strip() in content:
            return True
        return False
    with open(smali_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return True


def inject_dialog_main():
    """
    Inject DEX as next classesN.dex + hook into Activity onCreate/onResume.
    Credit: MMK MOD
    """
    banner("INJECT DIALOG", "MMK MOD  •  dex + hook onCreate/onResume")
    info("Credit: MMK MOD")
    print()

    # Session: hanya sisip hook smali ke folder decompile (dex inject butuh APK utuh)
    if mmk_session_active():
        dec = MMK_SESSION["dec"]
        mmk_session_print_bar()
        banner("INJECT (SESSION)", "hook onCreate/onResume di smali · build ditunda")
        activity = input(f"  {C.CYAN}Activity{C.RESET} (com.app.MainActivity) ➤ ").strip()
        if not activity:
            warn("Activity kosong — skip inject di session")
            return
        print(f"  {C.DIM}Contoh: invoke-static {{p0}}, Lcom/zx/zendialogs/Zxdialogs;->show(Landroid/content/Context;)V{C.RESET}")
        hook = input(f"  {C.CYAN}Hook code{C.RESET} ➤ ").strip()
        if not hook:
            warn("Hook kosong — skip")
            return
        smali_rel = _activity_to_smali_path(activity)
        found = None
        for root, _, files in os.walk(dec):
            for fn in files:
                if not fn.endswith(".smali"):
                    continue
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, dec).replace("\\", "/")
                if smali_rel in rel or fn == os.path.basename(smali_rel):
                    found = full
                    break
            if found:
                break
        if not found:
            err(f"Activity smali tidak ketemu: {smali_rel}")
            return
        if _inject_hook_into_smali(found, hook):
            ok(f"Hook injected → {os.path.relpath(found, dec)}")
            mmk_session_log("inject")
            ok("⏸ build ditunda sampai akhir batch")
        else:
            err("Inject hook gagal")
        return

    if not shutil.which('java'):
        err("Java diperlukan (APKEditor decompile/build)")
        return

    jar = None
    if '_smali_ensure_apkeditor' in globals():
        jar = _smali_ensure_apkeditor()
    else:
        for f in os.listdir('.'):
            if f.lower().endswith('.jar') and 'apkeditor' in f.lower():
                jar = f
                break
    if not jar:
        err("APKEditor.jar tidak ditemukan")
        return
    jar_abs = os.path.abspath(jar)

    apk = _pick_files_by_ext(('.apk',), "SELECT APK  •  INJECT")
    if not apk:
        return
    ok(f"APK: {os.path.basename(apk)}")

    dex = _pick_files_by_ext(('.dex',), "SELECT DEX  •  INJECT")
    if not dex:
        return
    ok(f"DEX: {os.path.basename(dex)}")

    next_dex = _next_classes_dex_name(apk)
    info(f"Akan disisipkan sebagai: {next_dex}")

    print()
    activity = input(
        f"  {C.CYAN}Activity{C.RESET} (contoh com.app.MainActivity) ➤ "
    ).strip()
    if not activity:
        err("Activity wajib diisi")
        return

    print()
    print(f"  {C.DIM}Contoh hook:{C.RESET}")
    print(f"  {C.DIM}invoke-static {{p0}}, Lcom/zx/zendialogs/Zxdialogs;->show(Landroid/content/Context;)V{C.RESET}")
    hook = input(f"  {C.CYAN}Hook code{C.RESET} ➤ ").strip()
    if not hook:
        err("Hook code wajib diisi")
        return

    work = os.getcwd()
    base = os.path.splitext(os.path.basename(apk))[0]
    work_apk = os.path.join(work, f"{base}-inject-tmp.apk")
    out_apk = os.path.join(work, f"{base}-dialog-injected.apk")
    dec_dir = os.path.join(work, f"{base}_inject_dec")

    shutil.copy2(apk, work_apk)

    # 1) Inject DEX into ZIP
    banner("INJECT DEX", f"{os.path.basename(dex)} → {next_dex}")
    spinner("Menulis DEX ke APK...", 0.8)
    tmp_zip = work_apk + ".zipnew"
    with zipfile.ZipFile(work_apk, 'r') as zin, zipfile.ZipFile(tmp_zip, 'w') as zout:
        for item in zin.infolist():
            if item.filename == next_dex:
                continue  # replace if exists
            zout.writestr(item, zin.read(item.filename))
        zout.write(dex, next_dex)
    os.replace(tmp_zip, work_apk)
    ok(f"DEX injected as {next_dex}")

    # 2) Decompile for smali hook
    if os.path.isdir(dec_dir):
        shutil.rmtree(dec_dir, ignore_errors=True)
    banner("DECOMPILE", "sisip hook di Activity")
    spinner("APKEditor decompile...", 1.5)
    rc = run_java_quiet(['java', '-jar', jar_abs, 'd', '-i', work_apk, '-o', dec_dir], label='DECOMPILE')
    if rc != 0 or not os.path.isdir(dec_dir):
        err("Decompile gagal")
        return

    smali_rel = _activity_to_smali_path(activity)
    # search in smali / smali_classes*
    found = None
    for root, dirs, files in os.walk(dec_dir):
        for fn in files:
            if not fn.endswith('.smali'):
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, dec_dir).replace('\\', '/')
            if rel.endswith(smali_rel) or rel.endswith('/' + smali_rel) or fn == os.path.basename(smali_rel):
                # prefer exact package path match
                if smali_rel in rel.replace('\\', '/'):
                    found = full
                    break
        if found:
            break

    if not found:
        # fuzzy: basename only
        bn = os.path.basename(smali_rel)
        for root, dirs, files in os.walk(dec_dir):
            if bn in files:
                found = os.path.join(root, bn)
                break

    if not found:
        err(f"Activity smali tidak ketemu: {smali_rel}")
        info("Cek nama package/activity (case-sensitive)")
        return

    ok(f"Smali: {os.path.relpath(found, dec_dir)}")
    spinner("Inject hook ke onCreate/onResume...", 0.8)
    if _inject_hook_into_smali(found, hook):
        ok("Hook injected")
    else:
        err("Gagal inject — onCreate/onResume tidak ditemukan")
        return

    # 3) Rebuild
    banner("BUILD", "APKEditor b")
    if os.path.exists(out_apk):
        try:
            os.remove(out_apk)
        except Exception:
            pass
    spinner("Building...", 1.5)
    rc = run_java_quiet(['java', '-jar', jar_abs, 'b', '-i', dec_dir, '-o', out_apk, '-f'], label="BUILD")
    if rc != 0 or not os.path.exists(out_apk):
        err("Build gagal")
        return

    # cleanup tmp
    try:
        os.remove(work_apk)
    except Exception:
        pass
    ans = input(f"  {C.YELLOW}Hapus folder decompile? [y/N]{C.RESET} ➤ ").strip().lower()
    if ans in ('y', 'ya', 'yes', '1'):
        shutil.rmtree(dec_dir, ignore_errors=True)

    print()
    print(f"  {C.MAGENTA}╔{'═'*50}╗{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}{C.BOLD}{C.GREEN}{'INJECT DIALOG COMPLETE — MMK MOD'.center(50)}{C.RESET}{C.MAGENTA}║{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  Output : {C.CYAN}{os.path.basename(out_apk)}{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  DEX    : {next_dex}")
    print(f"  {C.MAGENTA}║{C.RESET}  Hook   : {activity}")
    print(f"  {C.MAGENTA}╚{'═'*50}╝{C.RESET}")
    info("Jangan lupa Sign APK (menu 6) sebelum install")


def _hook_collect_rules():
    """
    Input interaktif daftar method yang akan di-hook (premium, dll).
    Return list dict: {cls, method, proto, action, value}
      action: true|false|void|int|custom
    """
    print()
    print(f"  {C.BOLD}{C.CYAN}DAFTAR HOOK{C.RESET}")
    print(f"  {C.DIM}Contoh premium:{C.RESET}")
    print(f"  {C.DIM}  Class  : com.example.UserManager{C.RESET}")
    print(f"  {C.DIM}  Method : isPremium / isVip / isPro{C.RESET}")
    print(f"  {C.DIM}  Proto  : ()Z{C.RESET}")
    print(f"  {C.DIM}  Action : true{C.RESET}")
    print()
    print(f"  {C.GREEN}1){C.RESET}  Input manual (satu per satu)")
    print(f"  {C.GREEN}2){C.RESET}  Load dari file hooks.txt")
    print(f"  {C.GREEN}3){C.RESET}  Template premium cepat (isPremium/isVip/isPro → true)")
    print()
    mode = input(f"  {C.MAGENTA}Pilih [1/2/3] ➤{C.RESET} ").strip() or "1"
    rules = []

    if mode == "2":
        fp = input(f"  {C.CYAN}Path hooks.txt ➤{C.RESET} ").strip().strip('"') or "hooks.txt"
        if not os.path.isfile(fp):
            err(f"File tidak ada: {fp}")
            return []
        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # format: class|method|proto|action|value
                parts = [p.strip() for p in line.split("|")]
                if len(parts) < 4:
                    continue
                rules.append({
                    "cls": parts[0],
                    "method": parts[1],
                    "proto": parts[2] if len(parts) > 2 else "()Z",
                    "action": parts[3].lower(),
                    "value": parts[4] if len(parts) > 4 else "",
                })
        ok(f"Loaded {len(rules)} rules dari file")
        return rules

    if mode == "3":
        base = input(f"  {C.CYAN}Package/class prefix (kosong=scan semua) ➤{C.RESET} ").strip()
        for m in ("isPremium", "isVip", "isVIP", "isPro", "isProVersion", "getIsPremium", "isPurchased", "isSubscribed"):
            rules.append({
                "cls": base or "*",
                "method": m,
                "proto": "()Z",
                "action": "true",
                "value": "",
            })
        ok(f"Template {len(rules)} method boolean → return true")
        return rules

    # manual
    print(f"  {C.DIM}Ketik kosong pada Class untuk selesai{C.RESET}")
    while True:
        cls = input(f"\n  {C.CYAN}Class{C.RESET} (com.app.Foo / * ) ➤ ").strip()
        if not cls:
            break
        method = input(f"  {C.CYAN}Method{C.RESET} ➤ ").strip()
        if not method:
            warn("Method kosong — skip")
            continue
        proto = input(f"  {C.CYAN}Proto{C.RESET} [()Z] ➤ ").strip() or "()Z"
        print(f"  Action: {C.GREEN}true{C.RESET} / false / void / int / custom")
        action = input(f"  {C.CYAN}Action{C.RESET} [true] ➤ ").strip().lower() or "true"
        value = ""
        if action == "int":
            value = input(f"  {C.CYAN}Nilai int{C.RESET} [1] ➤ ").strip() or "1"
        elif action == "custom":
            print(f"  {C.DIM}Tempel body smali (akhiri dengan baris: END){C.RESET}")
            lines = []
            while True:
                ln = input()
                if ln.strip() == "END":
                    break
                lines.append(ln)
            value = "\n".join(lines)
        rules.append({
            "cls": cls,
            "method": method,
            "proto": proto,
            "action": action,
            "value": value,
        })
        ok(f"+ {cls}.{method}{proto} → {action}")
    return rules


def _hook_smali_body(action, value, proto):
    """
    Generate smali method body (tanpa .method/.end method).

    WAJIB pakai .locals — bukan .registers!
    Instance method isPremium()Z punya p0=this.
    .registers 1 = hanya p0, tidak ada v0 → error APKEditor:
      Register v0 is NOT local register
    .locals 1 = v0 lokal + param tetap ada → OK.
    """
    action = (action or "true").lower()
    if action == "custom" and value:
        body = value if value.endswith("\n") else value + "\n"
        if ".locals" not in body and ".registers" not in body:
            body = "    .locals 1\n\n" + body
        return body
    if action == "void" or proto.endswith(")V"):
        return "    .locals 0\n\n    return-void\n"
    if action == "false":
        return "    .locals 1\n\n    const/4 v0, 0x0\n\n    return v0\n"
    if action == "int":
        try:
            n = int(value or "1")
        except Exception:
            n = 1
        if -8 <= n <= 7:
            return f"    .locals 1\n\n    const/4 v0, {n}\n\n    return v0\n"
        return f"    .locals 1\n\n    const v0, {n}\n\n    return v0\n"
    if proto.endswith(")Z") or action == "true":
        return "    .locals 1\n\n    const/4 v0, 0x1\n\n    return v0\n"
    if "Ljava/" in proto or proto.endswith(";") or action == "null":
        return "    .locals 1\n\n    const/4 v0, 0x0\n\n    return-object v0\n"
    return "    .locals 1\n\n    const/4 v0, 0x1\n\n    return v0\n"



def _hook_patch_smali_methods(dec_dir, rules):
    """
    Cari method di smali sesuai rules, ganti body.
    Return (patched_count, details[])
    """
    smali_files = []
    for root, _, fs in os.walk(dec_dir):
        for fn in fs:
            if fn.endswith(".smali"):
                smali_files.append(os.path.join(root, fn))

    # method regex
    method_re = re.compile(
        r"(\.method\s+[^\n]*\s+(\S+)\(([^)]*)\)(\S+)\s*\n)([\s\S]*?)(\n\.end method)",
        re.MULTILINE,
    )
    patched = 0
    details = []

    for fp in smali_files:
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue
        # class name from .class line
        cm = re.search(r"\.class\s+[^\n]*\s+L([^;]+);", content)
        class_java = cm.group(1).replace("/", ".") if cm else ""
        class_path = cm.group(1) if cm else ""

        original = content

        def replacer(m):
            nonlocal patched
            full_head, name, params, ret, body, end = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), m.group(6)
            proto = f"({params}){ret}"
            for rule in rules:
                rcls = rule["cls"]
                if rcls not in ("*", ""):
                    # match java or slash form
                    rc = rcls.replace(".", "/")
                    if rcls != class_java and rc != class_path and not class_java.endswith("." + rcls) and rcls not in class_java:
                        continue
                if rule["method"] != name:
                    continue
                rp = rule.get("proto") or ""
                if rp and rp not in ("*", "") and rp != proto:
                    # allow ()Z match if rule says ()Z
                    if rp.replace(" ", "") != proto.replace(" ", ""):
                        continue
                new_body = _hook_smali_body(rule["action"], rule.get("value", ""), proto)
                patched += 1
                details.append(f"{class_java}.{name}{proto} → {rule['action']}")
                return full_head + new_body + end
            return m.group(0)

        content2 = method_re.sub(replacer, content)
        if content2 != original:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(content2)

    return patched, details


def _hook_export_pine_java(rules, out_path):
    """Generate sample Pine Java code for Android Studio (referensi)."""
    lines = [
        "// Auto-generated by MMK MOD — referensi Pine hook",
        "// https://github.com/canyie/pine",
        "//",
        "// dependencies { implementation 'top.canyie.pine:core:0.3.0' }",
        "//",
        "import top.canyie.pine.Pine;",
        "import top.canyie.pine.callback.MethodReplacement;",
        "",
        "public class MmkPineHooks {",
        "    public static void install() {",
        "        try {",
    ]
    for r in rules:
        cls = r["cls"] if r["cls"] != "*" else "YOUR_CLASS"
        method = r["method"]
        action = r["action"]
        if action == "true":
            rep = "MethodReplacement.returnConstant(Boolean.TRUE)"
        elif action == "false":
            rep = "MethodReplacement.returnConstant(Boolean.FALSE)"
        elif action == "void":
            rep = "MethodReplacement.DO_NOTHING"
        elif action == "int":
            rep = f"MethodReplacement.returnConstant(Integer.valueOf({r.get('value') or 1}))"
        else:
            rep = "MethodReplacement.returnConstant(Boolean.TRUE)"
        lines.append(f"            // {cls}.{method}")
        lines.append(f"            Pine.hook(")
        lines.append(f"                Class.forName(\"{cls}\").getDeclaredMethod(\"{method}\"),")
        lines.append(f"                {rep}")
        lines.append(f"            );")
    lines += [
        "        } catch (Throwable t) {",
        "            t.printStackTrace();",
        "        }",
        "    }",
        "}",
        "",
    ]
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out_path


def hook_app_main():
    """
    Hook method di APK (premium / custom).

    Bukan inject zip jadi — user INPUT method yang mau di-hook.

    Mode kerja (praktis di Termux tanpa Android Studio):
      → Decompile APK → ganti body method target → build
      (efek sama: isPremium() selalu true, dll)

    Pine (https://github.com/canyie/pine):
      → Script juga men-generate file Java contoh MmkPineHooks.java
        agar bisa di-compile di Android Studio jika butuh runtime Pine.

    Credit: MMK MOD
    """
    banner("HOOK APP", "MMK MOD  •  input method  •  premium / custom")
    info("Credit: MMK MOD")
    info("Pine ref: https://github.com/canyie/pine")
    print()
    print(f"  {C.BOLD}Cara kerja{C.RESET}")
    print(f"  {C.DIM}1. Kamu input class + method (mis. isPremium){C.RESET}")
    print(f"  {C.DIM}2. Script patch body method di smali (return true/false/void){C.RESET}")
    print(f"  {C.DIM}3. Build APK + generate contoh kode Pine Java{C.RESET}")
    print()

    if not shutil.which("java"):
        err("Java diperlukan")
        return
    jar = None
    try:
        jar = _find_or_fetch_apkeditor() if "_find_or_fetch_apkeditor" in globals() else None
    except Exception:
        pass
    if not jar:
        try:
            jar = _smali_ensure_apkeditor()
        except Exception:
            pass
    if not jar:
        for f in os.listdir("."):
            if f.lower().endswith(".jar") and "apkeditor" in f.lower():
                jar = os.path.abspath(f)
                break
    if not jar:
        err("APKEditor.jar tidak ditemukan")
        return
    jar_abs = os.path.abspath(jar)
    ok(f"APKEditor: {os.path.basename(jar_abs)}")

    entries = mmk_list_apks((".apk",))
    if not entries:
        err(f"Tidak ada .apk di {MMK_APP_DIR}")
        return
    apk_path = select_target(entries, title="SELECT APK  •  HOOK") if "select_target" in globals() else os.path.abspath(apks[0])
    if not apk_path:
        return
    apk_path = os.path.abspath(apk_path)
    ok(f"Target: {os.path.basename(apk_path)}")

    rules = _hook_collect_rules()
    if not rules:
        err("Tidak ada rule hook")
        return

    print()
    info(f"Total rule: {len(rules)}")
    for r in rules[:12]:
        print(f"  {C.CYAN}•{C.RESET} {r['cls']}.{r['method']}{r.get('proto','')} → {r['action']}")
    if len(rules) > 12:
        print(f"  {C.DIM}... +{len(rules)-12} lagi{C.RESET}")

    # export pine java sample always
    pine_java = os.path.abspath("MmkPineHooks.java")
    _hook_export_pine_java(rules, pine_java)
    ok(f"Contoh Pine Java: {pine_java}")

    # save rules
    rules_file = os.path.abspath("hooks_mmk.txt")
    with open(rules_file, "w", encoding="utf-8") as f:
        f.write("# class|method|proto|action|value\n")
        for r in rules:
            f.write(f"{r['cls']}|{r['method']}|{r.get('proto','()Z')}|{r['action']}|{r.get('value','')}\n")
    ok(f"Rules saved: {rules_file}")

    t0 = time.time()
    base = os.path.splitext(os.path.basename(apk_path))[0]
    dec = os.path.abspath(f"_mmk_hook_{int(time.time())}")
    out_apk = os.path.abspath(f"{base}-hooked.apk")
    if os.path.isdir(dec):
        shutil.rmtree(dec, ignore_errors=True)

    banner("DECOMPILE", "APKEditor d")
    spinner("Decompile...", 1.0)
    rc = run_java_quiet(["java", "-jar", jar_abs, "d", "-i", apk_path, "-o", dec, "-f"], label="DECOMPILE")
    if rc != 0 or not os.path.isdir(dec):
        err("Decompile gagal")
        return

    banner("PATCH METHOD", "ganti body sesuai rule")
    n, details = _hook_patch_smali_methods(dec, rules)
    if n == 0:
        warn("Tidak ada method yang cocok di smali")
        warn("Cek nama class/method (case-sensitive) atau pakai Class=* ")
        shutil.rmtree(dec, ignore_errors=True)
        return
    ok(f"Patched {n} method(s)")
    for d in details[:20]:
        print(f"  {C.GREEN}✓{C.RESET} {d}")
    if len(details) > 20:
        print(f"  {C.DIM}... +{len(details)-20}{C.RESET}")

    banner("BUILD", "APKEditor b")
    if os.path.exists(out_apk):
        try:
            os.remove(out_apk)
        except Exception:
            pass
    spinner("Build...", 1.0)
    rc = run_java_quiet(["java", "-jar", jar_abs, "b", "-i", dec, "-o", out_apk, "-f"], label="BUILD")
    if rc != 0 or not os.path.isfile(out_apk):
        run_java_quiet(["java", "-jar", jar_abs, "b", "-i", dec, "-o", out_apk, "-f"], label="BUILD")
    shutil.rmtree(dec, ignore_errors=True)

    if not os.path.isfile(out_apk):
        err("Build gagal")
        return

    dt = time.time() - t0
    try:
        sz = human_size(os.path.getsize(out_apk))
    except Exception:
        sz = "-"

    print()
    print(f"  {C.MAGENTA}╔{'═'*52}╗{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}{C.BOLD}{C.GREEN}{'HOOK COMPLETE — MMK MOD'.center(52)}{C.RESET}{C.MAGENTA}║{C.RESET}")
    print(f"  {C.MAGENTA}╠{'═'*52}╣{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  Output  : {C.CYAN}{os.path.basename(out_apk)}{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  Patched : {n} method(s)")
    print(f"  {C.MAGENTA}║{C.RESET}  Size    : {sz}")
    print(f"  {C.MAGENTA}║{C.RESET}  Time    : {dt:.1f}s")
    print(f"  {C.MAGENTA}║{C.RESET}  Pine.js : {os.path.basename(pine_java)} (contoh)")
    print(f"  {C.MAGENTA}╚{'═'*52}╝{C.RESET}")
    warn("Sign (menu 6) sebelum install")
    info("Runtime Pine penuh butuh compile di Android Studio — lihat MmkPineHooks.java")


def apks_to_apk_main():
    """
    APKS / XAPK → APK  (MMK MOD)
    Mode 1: Extract base.apk (pertahankan signature asli)
    Mode 2: Full merge via APKEditor (semua split digabung)
    Input: menu/app  ·  Output: menu/out/app
    """
    global MMK_PRESET_OPTIONS
    mmk_ensure_dirs()
    banner("APKS → APK", "MMK MOD  •  antisplit / merge")
    info("Credit: MMK MOD")
    box_info([
        f"Input  : {MMK_APP_DIR}",
        f"Output : {MMK_OUT_APP}",
        f"Files  : {MMK_FILES_DIR}",
    ], title="PATH")
    print()

    # mode — bisa dari preset multibypass
    preset = (globals().get("MMK_PRESET_OPTIONS") or {}).get("9")
    if preset in ("1", "2"):
        mode = preset
        ok(f"Mode preset (multibypass): {mode}")
    else:
        print(f"  {C.BOLD}{C.CYAN}▶ MODE{C.RESET}")
        print(f"     {C.GREEN}1){C.RESET}  Extract base.apk     {C.DIM}— signature asli tetap{C.RESET}")
        print(f"     {C.GREEN}2){C.RESET}  Full merge (APKEditor) {C.DIM}— gabung semua split{C.RESET}")
        print(f"     {C.RED}0){C.RESET}  Back")
        print()
        mode = input(f"  {C.MAGENTA}𝙿𝚒𝚕𝚒𝚑 𝚗𝚘𝚖𝚘𝚛 ➤{C.RESET} ").strip()
        if mode in ("0", ""):
            return
        if mode not in ("1", "2"):
            warn("Pilihan tidak valid")
            return

    # select apks/xapk — refresh path + scan semua lokasi menu/app
    _mmk_init_paths()
    mmk_ensure_dirs()
    files = mmk_list_apks((".apks", ".xapk", ".apkm"))
    if not files:
        # coba juga .apk (kadang user salah format) + tampilkan path yang di-scan
        any_apk = mmk_list_apks((".apk", ".apks", ".xapk", ".apkm"))
        err(f"Tidak ada file .apks / .xapk / .apkm")
        info(f"APP dir : {MMK_APP_DIR}")
        info(f"ROOT    : {MMK_ROOT}")
        info("Letakkan .apks di: menu/app/  (bukan folder out/)")
        if any_apk:
            warn(f"Ketemu {len(any_apk)} .apk (bukan .apks) di app/")
            for _, n, sz in any_apk[:5]:
                print(f"  {C.DIM}· {n} ({human_size(sz)}){C.RESET}")
        return

    if "select_target" in globals():
        chosen = select_target(files, title="SELECT TARGET  •  APKS/XAPK")
        if not chosen:
            return
        input_path = chosen
    else:
        input_path = files[0][0]

    name = os.path.basename(input_path)
    ok(f"Input: {name}")
    stem = Path(name).stem
    default_out = f"{stem}.apk"
    # output ke out/app kecuali preset multibypass (otomatis)
    if preset in ("1", "2"):
        out_name = default_out
    else:
        print()
        out_name = input(f"  {C.CYAN}Output APK{C.RESET} [{C.DIM}{default_out}{C.RESET}] ➤ ").strip() or default_out
    if not out_name.lower().endswith(".apk"):
        out_name += ".apk"
    out_path = mmk_output("app", out_name)
    # juga path kerja jika out gagal tulis
    work_out = os.path.abspath(out_name)

    t0 = time.time()

    if mode == "1":
        banner("EXTRACT BASE", "signature asli dipertahankan")
        if not zipfile.is_zipfile(input_path):
            err("File bukan ZIP/APKS valid")
            return
        tmp = tempfile.mkdtemp(prefix="mmk_apks_")
        try:
            spinner("Extract APKS...", 0.8)
            with zipfile.ZipFile(input_path, "r") as z:
                z.extractall(tmp)
            ok(f"Extract → temp")

            apk_list = []
            for root, _, fs in os.walk(tmp):
                for f in fs:
                    if f.lower().endswith(".apk"):
                        fp = os.path.join(root, f)
                        apk_list.append((f, fp, os.path.getsize(fp)))
                        print(f"  {C.CYAN}◆{C.RESET} {f}  {C.DIM}{human_size(os.path.getsize(fp))}{C.RESET}")

            if not apk_list:
                err("Tidak ada .apk di dalam APKS")
                return

            # prefer base.apk
            base = None
            for n, fp, sz in apk_list:
                if n.lower() == "base.apk":
                    base = (n, fp, sz)
                    break
            if not base:
                # largest
                base = max(apk_list, key=lambda x: x[2])
                warn(f"base.apk tidak ada — pakai terbesar: {base[0]}")

            spinner(f"Copy {base[0]} → {out_name}...", 0.5)
            try:
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                shutil.copy2(base[1], out_path)
            except Exception:
                shutil.copy2(base[1], work_out)
                out_path = work_out
            ok(f"Output: {os.path.basename(out_path)} ({human_size(os.path.getsize(out_path))})")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    else:
        # Full merge APKEditor
        banner("FULL MERGE", "APKEditor m -i apks -o apk")
        if not shutil.which("java"):
            err("Java diperlukan untuk full merge")
            info("Atau pilih mode 1 (extract base.apk)")
            return
        jar = None
        if "_smali_ensure_apkeditor" in globals():
            try:
                jar = _smali_ensure_apkeditor()
            except Exception:
                jar = None
        if not jar:
            for d in (MMK_FILES_DIR, MMK_ROOT, os.getcwd()):
                if not d or not os.path.isdir(d):
                    continue
                try:
                    for f in os.listdir(d):
                        if f.lower().endswith(".jar") and "apkeditor" in f.lower():
                            jar = os.path.join(d, f)
                            break
                except OSError:
                    pass
                if jar:
                    break
        if not jar:
            err("APKEditor.jar tidak ditemukan")
            info(f"Letakkan di: {MMK_FILES_DIR}")
            return
        jar_abs = os.path.abspath(jar)
        for p in (out_path, work_out):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
        spinner("Merging splits (bisa lama)...", 1.5)
        # tulis ke work dulu, lalu pindah ke out/app
        rc = run_java_quiet(["java", "-jar", jar_abs, "m", "-i", input_path, "-o", work_out, "-f"], label="MERGE")
        found = None
        for c in (work_out, out_path):
            if c and os.path.isfile(c) and os.path.getsize(c) > 1000:
                found = c
                break
        if rc != 0 or not found:
            err("Merge gagal")
            return
        try:
            if os.path.abspath(found) != os.path.abspath(out_path):
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                shutil.move(found, out_path)
            found = out_path
        except Exception:
            out_path = found
        ok(f"Merged: {os.path.basename(out_path)} ({human_size(os.path.getsize(out_path))})")

    dur = time.time() - t0
    out_dir = os.path.dirname(os.path.abspath(out_path)) or os.getcwd()
    print()
    print(f"  {C.MAGENTA}╔{'═'*58}╗{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}{C.BOLD}{C.GREEN}{'APKS → APK DONE — MMK MOD'.center(58)}{C.RESET}{C.MAGENTA}║{C.RESET}")
    print(f"  {C.MAGENTA}╠{'═'*58}╣{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  Output    : {C.CYAN}{os.path.basename(out_path)}{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  Mode      : {'extract base' if mode == '1' else 'full merge'}")
    print(f"  {C.MAGENTA}║{C.RESET}  Time      : {dur:.1f}s")
    print(f"  {C.MAGENTA}║{C.RESET}  Direktori : {C.CYAN}{out_dir[:44]}{C.RESET}")
    print(f"  {C.MAGENTA}╚{'═'*58}╝{C.RESET}")
    if mode == "1":
        info("Mode extract: signature asli base.apk — config/split lain mungkin hilang")
    else:
        info("Mode merge: biasanya perlu Sign ulang (menu 6)")




def about_mmk():
    """Tampilkan info & sosial media MMK MOD."""
    _clear()
    banner("ABOUT  •  MMK MOD", "sosial media & channel resmi")
    print()
    print(f"  {C.BOLD}{C.CYAN}╔{'═'*52}╗{C.RESET}")
    print(f"  {C.CYAN}║{C.RESET}  {C.BOLD}{C.WHITE}MMK MOD  —  All-in-One Patch Suite{C.RESET}")
    print(f"  {C.CYAN}║{C.RESET}  {C.DIM}Flutter · Hermes · Smali · MTCR · Toolkit{C.RESET}")
    print(f"  {C.CYAN}╠{'═'*52}╣{C.RESET}")
    print(f"  {C.CYAN}║{C.RESET}")
    print(f"  {C.CYAN}║{C.RESET}  {C.GREEN}▶ Grup WhatsApp{C.RESET}")
    print(f"  {C.CYAN}║{C.RESET}    {C.WHITE}https://chat.whatsapp.com/LDzlBOXR3I12Rb79oy5TFJ{C.RESET}")
    print(f"  {C.CYAN}║{C.RESET}")
    print(f"  {C.CYAN}║{C.RESET}  {C.GREEN}▶ Saluran Mod APK{C.RESET}")
    print(f"  {C.CYAN}║{C.RESET}    {C.WHITE}https://whatsapp.com/channel/0029Vb7vQrL1yT22MFrBrR42{C.RESET}")
    print(f"  {C.CYAN}║{C.RESET}")
    print(f"  {C.CYAN}║{C.RESET}  {C.GREEN}▶ Saluran Tanya Jawab{C.RESET}")
    print(f"  {C.CYAN}║{C.RESET}    {C.WHITE}https://whatsapp.com/channel/0029Vb7i2omLNSa3VM8Chc1A{C.RESET}")
    print(f"  {C.CYAN}║{C.RESET}")
    print(f"  {C.CYAN}║{C.RESET}  {C.GREEN}▶ Web Official{C.RESET}")
    print(f"  {C.CYAN}║{C.RESET}    {C.WHITE}https://botl71193-debug.github.io/Modapks/{C.RESET}")
    print(f"  {C.CYAN}║{C.RESET}")
    print(f"  {C.CYAN}╚{'═'*52}╝{C.RESET}")
    print()
    info("Thanks for using MMK MOD")


def _mmk_feature_catalog():
    """Daftar fitur yang bisa dijalankan Multibypass (nomor = menu utama)."""
    return [
        ("1", "Flutter Patcher",      "libapp.so / blutter",     "flutter_main"),
        ("2", "Hermes Patcher",       "index.android.bundle",   "hermes_main"),
        ("3", "Smali Patcher",        "dex / premium / license","smali_main"),
        ("4", "MTCR Apply Tool",      "single / batch / backup","_run_mtcr"),
        ("5", "Nexus Cloud Toolkit",  "JNI / Blutter / Offset", "toolkit_main"),
        ("6", "Sign APK",             ".jks / .keystore",       "sign_apk_main"),
        ("7", "Protect APK",          "DEX HIGH DPT/Smali",     "protect_apk_main"),
        ("8", "Inject Dialog",        "dex + onCreate hook",    "inject_dialog_main"),
        ("9", "APKS → APK",           "antisplit / merge",      "apks_to_apk_main"),
        ("10", "PairIP Bypass",       "license / manifest",     "pairip_bypass_main"),
        ("18", "REGEX PRO",           "Ads / Lazy / Anti-SS",   "ads_regex_main"),
        ("21", "DEX Anti-Bingung",    "clean nop/debug junk",   "dex_anti_confusion_main"),
    ]


def _run_mtcr():
    """Wrapper MTCR agar bisa dipanggil dari multibypass."""
    global CONFIG, USE_COLORS, VERBOSE, DRY_RUN
    CONFIG = load_config()
    USE_COLORS = CONFIG.get("use_colors", True) and supports_color()
    VERBOSE = CONFIG.get("verbose_mode", False)
    DRY_RUN = False
    setup_logging()
    if not check_python():
        return
    if not check_java():
        return
    check_disk_space(silent=True)
    main_menu()


def _dispatch_feature(key: str):
    """Jalankan satu fitur by nomor menu."""
    mapping = {
        "1": flutter_main,
        "2": hermes_main,
        "3": smali_main,
        "4": _run_mtcr,
        "5": toolkit_main,
        "6": sign_apk_main,
        "7": protect_apk_main,
        "8": inject_dialog_main,
        "9": apks_to_apk_main,
        "10": pairip_bypass_main,
        "18": ads_regex_main,
        "21": dex_anti_confusion_main,
    }
    fn = mapping.get(key)
    if not fn:
        warn(f"Nomor tidak dikenal: {key}")
        return False
    try:
        fn()
        return True
    except SystemExit:
        return True
    except KeyboardInterrupt:
        warn(f"Dibatalkan di fitur {key}")
        return False
    except Exception as e:
        err(f"Error fitur {key}: {e}")
        import traceback
        traceback.print_exc()
        return False


MMK_HISTORY_FILE = "mmk_history.json"


def _mmk_history_load():
    candidates = [MMK_HISTORY_FILE]
    try:
        candidates.append(os.path.join(MMK_ROOT, "mmk_history.json"))
    except Exception:
        pass
    for fp in candidates:
        try:
            if os.path.isfile(fp):
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            continue
    return []


def _mmk_history_save(entry):
    """Tambah 1 entri history (max 100)."""
    try:
        # simpan di ROOT + cwd
        hist = _mmk_history_load()
        hist.insert(0, entry)
        hist = hist[:100]
        paths = [MMK_HISTORY_FILE]
        try:
            paths.append(os.path.join(MMK_ROOT, "mmk_history.json"))
        except Exception:
            pass
        for fp in paths:
            try:
                parent = os.path.dirname(os.path.abspath(fp))
                if parent:
                    os.makedirs(parent, exist_ok=True)
                with open(fp, "w", encoding="utf-8") as f:
                    json.dump(hist, f, indent=2, ensure_ascii=False)
            except Exception:
                continue
    except Exception as e:
        warn(f"Gagal simpan history: {e}")


def mmk_history_add(kind, path=None, extra=None, error=None, patches=None):
    """
    API seragam untuk semua fitur.
    kind: flutter/hermes/protect/error/...
    patches: list of dict {hex, set_to, keyword} atau string
    error: string error → dicatat di history
    """
    from datetime import datetime as _dt
    extra = extra or {}
    app = os.path.basename(path) if path else extra.get("app_name", "-")
    size = "-"
    if path and os.path.isfile(path):
        try:
            size = human_size(os.path.getsize(path))
        except Exception:
            pass
    entry = {
        "time": _dt.now().strftime("%Y-%m-%d %H:%M:%S"),
        "app_name": app,
        "size": size,
        "sign_status": _apk_sign_status(path) if path and str(path).lower().endswith(".apk") else "-",
        "elapsed": extra.get("elapsed", "-"),
        "steps": extra.get("steps", kind),
        "steps_detail": extra.get("steps_detail", [kind]),
        "modified": extra.get("modified", []),
        "patches": patches or extra.get("patches") or [],
        "ok": extra.get("ok", 0 if error else 1),
        "fail": extra.get("fail", 1 if error else 0),
        "total": extra.get("total", 1),
        "path": path or "",
        "kind": kind,
        "error": error,
        "patch_kind": extra.get("patch_kind", kind),
    }
    _mmk_history_save(entry)
    return entry


def print_patch_table(rows, title="PATCH DITEMUKAN"):
    """
    rows: list of dict atau tuple
      {hex, set_to, keyword}  atau  (hex, set_to, keyword)
    Tampil:
      Hex            | atur ke | keyword
      0x1234567      | TRUE    | isPremium
    """
    if not rows:
        return
    norm = []
    for r in rows:
        if isinstance(r, dict):
            h = str(r.get("hex") or r.get("addr") or r.get("offset") or "-")
            s = str(r.get("set_to") or r.get("value") or r.get("to") or "-")
            k = str(r.get("keyword") or r.get("kw") or r.get("name") or "-")
        elif isinstance(r, (list, tuple)) and len(r) >= 3:
            h, s, k = str(r[0]), str(r[1]), str(r[2])
        else:
            h, s, k = str(r), "-", "-"
        norm.append((h, s, k))
    print()
    print(f"  {C.CYAN}┌{'─'*18}┬{'─'*10}┬{'─'*28}┐{C.RESET}")
    print(f"  {C.CYAN}│{C.RESET}{C.YELLOW}{' Hex':<18}{C.RESET}{C.CYAN}│{C.RESET}{C.YELLOW}{' atur ke':<10}{C.RESET}{C.CYAN}│{C.RESET}{C.YELLOW}{' keyword':<28}{C.RESET}{C.CYAN}│{C.RESET}")
    print(f"  {C.CYAN}├{'─'*18}┼{'─'*10}┼{'─'*28}┤{C.RESET}")
    for h, s, k in norm:
        hs = h if len(h) <= 16 else h[:13] + "..."
        ss = s if len(s) <= 8 else s[:8]
        ks = k if len(k) <= 26 else k[:23] + "..."
        col = C.GREEN if s.upper() in ("TRUE", "0x1", "1") else (C.RED if s.upper() in ("FALSE", "0x0", "0") else C.CYAN)
        print(f"  {C.CYAN}│{C.RESET} {C.WHITE}{hs:<16}{C.RESET} {C.CYAN}│{C.RESET} {col}{ss:<8}{C.RESET} {C.CYAN}│{C.RESET} {ks:<26} {C.CYAN}│{C.RESET}")
    print(f"  {C.CYAN}└{'─'*18}┴{'─'*10}┴{'─'*28}┘{C.RESET}")
    print(f"  {C.DIM}Σ {len(norm)} offset  ·  {title}{C.RESET}")
    print()



def _apk_sign_status(path):
    """Cek apakah APK sudah ditandatangani. Return teks status."""
    if not path or not os.path.isfile(path):
        return "File tidak ada"
    try:
        with zipfile.ZipFile(path, "r") as z:
            names = [n.upper() for n in z.namelist()]
            has_rsa = any(
                n.startswith("META-INF/") and (n.endswith(".RSA") or n.endswith(".DSA") or n.endswith(".EC"))
                for n in names
            )
            has_sf = any(n.startswith("META-INF/") and n.endswith(".SF") for n in names)
            has_mf = any(n == "META-INF/MANIFEST.MF" for n in names)
            if has_rsa and has_sf:
                return "Signed ✓"
            if has_mf:
                return "Partial (MANIFEST saja)"
            return "Unsigned ✗"
    except Exception as e:
        return f"Unknown ({e})"


def _newest_apk_since(since_ts, exclude_paths=None):
    """Cari .apk terbaru di cwd + out/* yang dimodifikasi setelah since_ts."""
    exclude_paths = {os.path.abspath(p) for p in (exclude_paths or []) if p}
    best = None
    best_mtime = since_ts
    scan_dirs = [os.getcwd(), MMK_OUT_PROTECT, MMK_OUT_PATCHED, MMK_OUT_APP, MMK_OUT_INJECTED, MMK_APP_DIR]
    try:
        files_to_check = []
        for d in scan_dirs:
            if not d or not os.path.isdir(d):
                continue
            try:
                for f in os.listdir(d):
                    if f.lower().endswith(".apk"):
                        files_to_check.append(os.path.join(d, f))
            except OSError:
                continue
        for fp in files_to_check:
            fp = os.path.abspath(fp)
            if fp in exclude_paths:
                continue
            try:
                mt = os.path.getmtime(fp)
            except OSError:
                continue
            if mt > best_mtime:
                best_mtime = mt
                best = fp
    except Exception:
        pass
    return best


def _safe_remove_apk(path, protect_original):
    """Hapus APK intermediate; jangan hapus original user."""
    if not path:
        return False
    ap = os.path.abspath(path)
    po = os.path.abspath(protect_original) if protect_original else None
    if po and ap == po:
        return False
    if not os.path.isfile(ap):
        return False
    # hanya hapus hasil proses (nama khas) atau file di cwd yang bukan original
    try:
        os.remove(ap)
        warn(f"Hapus intermediate: {os.path.basename(ap)}")
        return True
    except Exception as e:
        warn(f"Gagal hapus {os.path.basename(ap)}: {e}")
        return False


def history_mmk_main():
    """
    List history run. Pilih nomor → detail:
    - list yang dimodif
    - estimasi/waktu
    - ok/fail (mis. 10/10)
    - patch ditemukan (Hermes/Flutter saja)
    """
    banner("HISTORY", "MMK MOD  •  log proses")
    hist = _mmk_history_load()
    if not hist:
        info("Belum ada history. Jalankan Multibypass / patch dulu.")
        return

    while True:
        print()
        print(f"  {C.CYAN}┌────┬────────────────────┬──────────────────────────┬──────────┬──────────┐{C.RESET}")
        print(f"  {C.CYAN}│{C.RESET}{C.YELLOW} NO {C.RESET}{C.CYAN}│{C.RESET}{C.YELLOW} WAKTU              {C.RESET}{C.CYAN}│{C.RESET}{C.YELLOW} APP                    {C.RESET}{C.CYAN}│{C.RESET}{C.YELLOW} HASIL  {C.RESET}{C.CYAN}│{C.RESET}{C.YELLOW} SIGN   {C.RESET}{C.CYAN}│{C.RESET}")
        print(f"  {C.CYAN}├────┼────────────────────┼──────────────────────────┼──────────┼──────────┤{C.RESET}")
        show = hist[:40]
        for i, e in enumerate(show, 1):
            ts = str(e.get("time", "-"))[:19]
            name = str(e.get("app_name", "-"))
            if len(name) > 24:
                name = name[:21] + "..."
            sign = str(e.get("sign_status", "-"))[:8]
            ok_n = e.get("ok", 0)
            fail_n = e.get("fail", 0)
            total = e.get("total", ok_n + fail_n)
            hasil = f"{ok_n}/{total}" if total else f"{ok_n}/{fail_n}"
            err_mark = "!" if e.get("error") else " "
            print(
                f"  {C.CYAN}│{C.RESET}{C.GREEN}{i:3d}{C.RESET}{C.CYAN}│{C.RESET} {ts:<18} {C.CYAN}│{C.RESET} {name:<24} {C.CYAN}│{C.RESET}"
                f" {C.YELLOW}{hasil:<8}{C.RESET}{C.CYAN}│{C.RESET} {sign:<8}{C.CYAN}│{C.RESET}{C.RED}{err_mark}{C.RESET}"
            )
        print(f"  {C.CYAN}└────┴────────────────────┴──────────────────────────┴──────────┴──────────┘{C.RESET}")
        print(f"  {C.DIM}Pilih NO = detail + tabel hex (Flutter/Hermes)  ·  ! = ada error log{C.RESET}")
        print(f"  {C.RED}0{C.RESET}  Kembali   {C.RED}99{C.RESET}  Hapus semua history")
        print()
        raw = input(f"  {C.MAGENTA}Pilih NO detail ➤{C.RESET} ").strip()
        if raw in ("0", "q", "exit", ""):
            return
        if raw in ("99", "clear", "hapus"):
            ans = input(f"  {C.YELLOW}Hapus SEMUA history? [y/N]{C.RESET} ➤ ").strip().lower()
            if ans in ("y", "ya", "yes", "1"):
                try:
                    if os.path.isfile(MMK_HISTORY_FILE):
                        os.remove(MMK_HISTORY_FILE)
                    ok("History dihapus")
                    hist = []
                except Exception as e:
                    err(str(e))
            if not hist:
                return
            continue
        try:
            idx = int(raw)
        except ValueError:
            warn("Masukkan nomor")
            continue
        if not (1 <= idx <= len(show)):
            warn("Nomor tidak valid")
            continue
        e = show[idx - 1]
        # ── DETAIL ──
        banner("HISTORY DETAIL", e.get("app_name", "entry"))
        print(f"  {C.BOLD}Nama app     :{C.RESET} {e.get('app_name', '-')}")
        print(f"  {C.BOLD}Size         :{C.RESET} {e.get('size', '-')}")
        print(f"  {C.BOLD}Status sign  :{C.RESET} {e.get('sign_status', '-')}")
        print(f"  {C.BOLD}Waktu run    :{C.RESET} {e.get('time', '-')}")
        print(f"  {C.BOLD}Durasi       :{C.RESET} {e.get('elapsed', e.get('duration', '-'))}")
        ok_n = e.get("ok", 0)
        fail_n = e.get("fail", 0)
        total = e.get("total", ok_n + fail_n)
        print(f"  {C.BOLD}Hasil        :{C.RESET} {C.GREEN}{ok_n}{C.RESET}/{total} berhasil  ·  {C.RED}{fail_n}{C.RESET} gagal")
        print(f"  {C.BOLD}Path         :{C.RESET} {C.DIM}{e.get('path', '-')}{C.RESET}")
        print()
        steps = e.get("steps_detail") or e.get("modified") or []
        if isinstance(steps, str):
            steps = [s.strip() for s in steps.replace("→", ",").split(",") if s.strip()]
        print(f"  {C.BOLD}{C.CYAN}▶ Yang dimodifikasi / step{C.RESET}")
        if steps:
            for j, s in enumerate(steps, 1):
                print(f"     {C.GREEN}{j}.{C.RESET} {s}")
        else:
            print(f"     {C.DIM}{e.get('steps', '-')}{C.RESET}")
        print()
        # Patch Flutter / Hermes — tabel Hex | atur ke | keyword
        patches = e.get("patches") or e.get("flutter_patches") or e.get("hermes_patches") or []
        print(f"  {C.BOLD}{C.MAGENTA}▶ Patch ditemukan (Flutter / Hermes){C.RESET}")
        if patches:
            # normalisasi ke dict rows
            rows = []
            for p in patches:
                if isinstance(p, dict):
                    rows.append(p)
                elif isinstance(p, (list, tuple)) and len(p) >= 3:
                    rows.append({"hex": p[0], "set_to": p[1], "keyword": p[2]})
                else:
                    rows.append({"hex": str(p), "set_to": "-", "keyword": "-"})
            print_patch_table(rows, title=e.get("patch_kind") or e.get("kind") or "history")
        else:
            kind = e.get("patch_kind", "")
            if kind:
                print(f"     {C.DIM}Jenis: {kind}{C.RESET}")
            else:
                print(f"     {C.DIM}(tidak ada / bukan Flutter-Hermes){C.RESET}")
        # error log
        if e.get("error"):
            print()
            print(f"  {C.BOLD}{C.RED}▶ Error log{C.RESET}")
            print(f"  {C.RED}{e.get('error')}{C.RESET}")
        # path + buka hex detail
        print()
        print(f"  {C.DIM}Direktori/path: {e.get('path', '-')}{C.RESET}")
        print()
        print(f"  {C.GREEN}1{C.RESET}  Lihat ulang tabel hex")
        print(f"  {C.GREEN}2{C.RESET}  Buka path di info (jika file masih ada)")
        print(f"  {C.RED}0{C.RESET}  Kembali ke list")
        sub = input(f"  {C.MAGENTA}➤{C.RESET} ").strip()
        if sub == "1" and patches:
            rows = []
            for p in patches:
                if isinstance(p, dict):
                    rows.append(p)
                elif isinstance(p, (list, tuple)) and len(p) >= 3:
                    rows.append({"hex": p[0], "set_to": p[1], "keyword": p[2]})
                else:
                    rows.append({"hex": str(p), "set_to": "-", "keyword": "-"})
            print_patch_table(rows, title="HEX DETAIL")
            input(f"  {C.YELLOW}Enter...{C.RESET}")
        elif sub == "2":
            path = e.get("path") or ""
            if path and os.path.isfile(path):
                ok(f"File ada: {path}")
                box_info([
                    f"File : {os.path.basename(path)}",
                    f"Size : {human_size(os.path.getsize(path))}",
                    f"Direktori : {os.path.dirname(os.path.abspath(path))}",
                    f"Sign : {_apk_sign_status(path)}",
                ], title="APK HISTORY")
            else:
                warn("File sudah tidak ada di path tersimpan")
            input(f"  {C.YELLOW}Enter...{C.RESET}")


# Fitur yang butuh decompile smali — digabung 1x decompile + 1x build di Multibypass
MMK_DECOMPILE_KEYS = frozenset({"3", "8", "10", "18"})  # Smali, Inject, PairIP, REGEX PRO


def multibypass_main():
    """
    Jalankan beberapa fitur berurutan.
    Smart batch: Smali + PairIP + Inject → decompile SEKALI, build SEKALI di akhir group.
    """
    global MMK_PRESELECTED_APK
    banner("MULTIBYPASS", "MMK MOD  •  smart decompile batch")
    info("APK dipilih sekali · fitur smali digabung (decompile 1x → build 1x)")
    print()

    entries = mmk_list_apks()
    if not entries:
        err(f"Tidak ada APK/APKS di {MMK_APP_DIR}")
        return

    prev_pre = MMK_PRESELECTED_APK
    MMK_PRESELECTED_APK = None
    chosen = select_target(entries, title="SELECT TARGET  •  MULTIBYPASS")
    if not chosen:
        MMK_PRESELECTED_APK = prev_pre
        info("Dibatalkan")
        return

    original_apk = os.path.abspath(chosen)
    MMK_PRESELECTED_APK = original_apk
    current_apk = original_apk
    ok(f"APK: {os.path.basename(MMK_PRESELECTED_APK)}")
    print()

    catalog = _mmk_feature_catalog()
    # UI keren
    print(f"  {C.MAGENTA}╔{'═'*58}╗{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}{C.BOLD}{'  NO   FITUR                      KETERANGAN'.ljust(58)}{C.RESET}{C.MAGENTA}║{C.RESET}")
    print(f"  {C.MAGENTA}╠{'═'*58}╣{C.RESET}")
    for num, name, desc, _ in catalog:
        tag = f" {C.YELLOW}[smali]{C.RESET}" if num in MMK_DECOMPILE_KEYS else ""
        line = f"  {num:<4} {name:<26} {desc}"
        # plain for width then color print
        print(f"  {C.MAGENTA}║{C.RESET}  {C.GREEN}{num:<4}{C.RESET} {C.WHITE}{name:<26}{C.RESET} {C.DIM}{desc}{C.RESET}")
        if num in MMK_DECOMPILE_KEYS:
            print(f"  {C.MAGENTA}║{C.RESET}       {C.YELLOW}↳ batch decompile{C.RESET}")
    print(f"  {C.MAGENTA}╚{'═'*58}╝{C.RESET}")
    print()
    print(f"  {C.DIM}Contoh:  3,10,8,6{C.RESET}")
    print(f"  {C.DIM}  → Smali+PairIP+Inject digabung (1 decompile) lalu Sign{C.RESET}")
    print(f"  {C.DIM}Contoh:  9,10,1,7{C.RESET}")
    print()

    raw = input(f"  {C.MAGENTA}Urutan fitur ➤{C.RESET} ").strip()
    if not raw:
        MMK_PRESELECTED_APK = None
        info("Dibatalkan")
        return

    parts = re.split(r"[,;\s]+", raw)
    seq = [p.strip() for p in parts if p.strip()]

    # ── Konfirmasi submenu di AWAL (sebelum eksekusi) ──
    global MMK_PRESET_OPTIONS
    MMK_PRESET_OPTIONS = {}
    SUBMENU_PROMPTS = {
        "7": {
            "title": "Protect APK — pilih mode",
            "options": [
                ("1", "SAFE", "resources only"),
                ("2", "MILD", "res + dex-level"),
                ("3", "DPT SAFE", "shell ringan"),
                ("4", "DPT MAX", "shell penuh"),
                ("5", "Smali High", "goto/nop"),
                ("6", "CyberArmor", "native packer"),
                ("7", "Dalvik Obf", "research NOP"),
                ("8", "ProGuard", "rename"),
            ],
        },
        "9": {
            "title": "APKS → APK — pilih mode",
            "options": [
                ("1", "Extract base.apk", "signature asli"),
                ("2", "Full merge", "APKEditor gabung split"),
            ],
        },
        "19": {
            "title": "Buka Proteksi — pilih level",
            "options": [
                ("1", "LOW", "decompile+rebuild"),
                ("2", "LOW+", "+ hapus NOP"),
                ("3", "MID", "+ normalize"),
                ("4", "HIGH", "+ strip debug"),
                ("5", "MAX", "agresif"),
            ],
        },
        "20": {
            "title": "Protect Script — tipe file",
            "options": [
                ("1", ".py", "marshal layers"),
                ("2", ".js", "minify/base64"),
                ("3", ".html", "minify + JS"),
                ("4", "Semua", "scan campuran"),
            ],
        },
        "18": {
            "title": "REGEX PRO — pilih grup",
            "options": [
                ("1", "Ads regex", "iklan"),
                ("2", "Patch Lazy", "lazy load"),
                ("3", "Anti-SS", "FLAG_SECURE bypass"),
            ],
        },
        "21": {
            "title": "DEX Anti-Bingung — pilih level",
            "options": [
                ("1", "RINGAN", "NOP beruntun"),
                ("2", "SEDANG", "+ strip debug"),
                ("3", "AGRESIF", "hapus hampir semua NOP"),
            ],
        },
    }
    need_sub = [k for k in seq if k in SUBMENU_PROMPTS]
    if need_sub:
        banner("KONFIRMASI SUBMENU", "isi dulu sebelum proses jalan")
        info("Fitur dengan submenu akan dikonfirmasi sekarang")
        print()
        for key in need_sub:
            meta = SUBMENU_PROMPTS[key]
            print(f"  {C.CYAN}┌─ [{key}] {meta['title']}{C.RESET}")
            for num, name, desc in meta["options"]:
                print(f"  {C.CYAN}│{C.RESET}  {C.GREEN}{num}){C.RESET} {name}  {C.DIM}{desc}{C.RESET}")
            print(f"  {C.CYAN}└────────────────────────{C.RESET}")
            while True:
                ans = input(f"  {C.MAGENTA}Pilih untuk fitur {key} ➤{C.RESET} ").strip()
                valid = {o[0] for o in meta["options"]}
                if ans in valid:
                    MMK_PRESET_OPTIONS[key] = ans
                    ok(f"Fitur {key} → opsi {ans}")
                    break
                warn("Pilihan tidak valid")
            print()
        # ringkasan
        print(f"  {C.BOLD}Ringkasan preset:{C.RESET}")
        for k, v in MMK_PRESET_OPTIONS.items():
            print(f"    {C.GREEN}{k}{C.RESET} → {v}")
        print()
        conf = input(f"  {C.YELLOW}Lanjut eksekusi urutan {','.join(seq)}? [Y/n] ➤{C.RESET} ").strip().lower()
        if conf in ("n", "no", "tidak"):
            MMK_PRESELECTED_APK = None
            MMK_PRESET_OPTIONS = {}
            info("Dibatalkan")
            return
    valid_ids = {c[0] for c in catalog}
    seq = [s for s in seq if s in valid_ids]

    if not seq:
        MMK_PRESELECTED_APK = None
        err("Tidak ada nomor valid")
        return

    name_map = {c[0]: c[1] for c in catalog}

    # ── Rencana: group consecutive decompile keys ──
    phases = []  # ("batch", [keys]) | ("single", key)
    i = 0
    while i < len(seq):
        if seq[i] in MMK_DECOMPILE_KEYS:
            batch = []
            while i < len(seq) and seq[i] in MMK_DECOMPILE_KEYS:
                batch.append(seq[i])
                i += 1
            phases.append(("batch", batch))
        else:
            phases.append(("single", seq[i]))
            i += 1

    print()
    print(f"  {C.BOLD}{C.CYAN}▶ RENCANA EKSEKUSI{C.RESET}")
    print(f"     APK: {C.GREEN}{os.path.basename(MMK_PRESELECTED_APK)}{C.RESET}")
    step_i = 0
    for kind, payload in phases:
        if kind == "batch":
            labels = " + ".join(name_map.get(k, k) for k in payload)
            print(f"     {C.YELLOW}◆ BATCH SMALI{C.RESET}  [{','.join(payload)}] {labels}")
            print(f"       {C.DIM}decompile 1x → patch {len(payload)}x → build 1x{C.RESET}")
            step_i += len(payload)
        else:
            step_i += 1
            print(f"     {C.YELLOW}{step_i}.{C.RESET} [{payload}] {name_map.get(payload, payload)}")
    print()
    conf = input(f"  {C.YELLOW}Jalankan? [y/N]{C.RESET} ➤ ").strip().lower()
    if conf not in ("y", "yes", "ya", "1"):
        MMK_PRESELECTED_APK = None
        info("Dibatalkan")
        return

    total = len(seq)
    ok_count = 0
    fail_count = 0
    step_labels = []
    step_detail = []
    patches_found = []
    t_run_start = time.time()
    prev_output = None
    global_step = 0

    try:
        for kind, payload in phases:
            if kind == "single":
                n = payload
                global_step += 1
                banner(f"STEP {global_step}/{total}", f"[{n}] {name_map.get(n, n)}")
                ok(f"APK: {os.path.basename(current_apk)}")
                t_before = time.time()
                success = _dispatch_feature(n)
                dt = time.time() - t_before
                if success:
                    ok_count += 1
                    label = name_map.get(n, n)
                    step_labels.append(label)
                    step_detail.append(f"{global_step}. {label} ({dt:.1f}s) ✓")
                    newest = _newest_apk_since(
                        t_before - 1.0,
                        exclude_paths=[p for p in [current_apk, original_apk, prev_output] if p],
                    )
                    if newest and os.path.abspath(newest) != os.path.abspath(current_apk):
                        old_input = os.path.abspath(current_apk)
                        current_apk = os.path.abspath(newest)
                        MMK_PRESELECTED_APK = current_apk
                        ok(f"APK hasil: {os.path.basename(current_apk)}")
                        if global_step >= 2 and old_input != original_apk:
                            _safe_remove_apk(old_input, protect_original=original_apk)
                        prev_output = current_apk
                    if n in ("1", "2"):
                        patches_found.append(f"[{label}] {os.path.basename(current_apk)} ({dt:.1f}s)")
                else:
                    fail_count += 1
                    step_detail.append(f"{global_step}. {name_map.get(n, n)} ({dt:.1f}s) ✗")
                    cont = input(f"  {C.YELLOW}Lanjut? [Y/n]{C.RESET} ➤ ").strip().lower()
                    if cont in ("n", "no", "tidak"):
                        break
                print()
                continue

            # ── BATCH: decompile 1x → patch each → build 1x ──
            batch = payload
            banner("BATCH SMALI", "decompile sekali · " + " + ".join(name_map.get(k, k) for k in batch))
            ok(f"APK: {os.path.basename(current_apk)}")
            info(f"Fitur batch: {', '.join(batch)}")
            t_batch = time.time()

            # pastikan jar + start session
            jar = None
            try:
                jar = _find_or_fetch_apkeditor()
            except Exception:
                pass
            if not jar:
                try:
                    jar = _smali_ensure_apkeditor()
                except Exception:
                    pass
            if not jar:
                err("APKEditor.jar diperlukan untuk batch smali")
                fail_count += len(batch)
                continue

            # merge apks if needed before session
            apk_for_session = current_apk
            if apk_for_session.lower().endswith((".apks", ".xapk")):
                merged = os.path.splitext(apk_for_session)[0] + "_merged.apk"
                run_java_quiet(["java", "-jar", jar, "m", "-i", apk_for_session, "-o", merged, "-f"], label="MERGE")
                if os.path.isfile(merged):
                    apk_for_session = os.path.abspath(merged)
                    current_apk = apk_for_session
                    MMK_PRESELECTED_APK = current_apk

            if mmk_session_active():
                mmk_session_abort()
            dec = mmk_session_start(apk_for_session, jar_abs=jar, force_new=True)
            if not dec:
                err("Decompile batch gagal")
                fail_count += len(batch)
                continue

            batch_ok = True
            for n in batch:
                global_step += 1
                label = name_map.get(n, n)
                print()
                step(global_step, total, f"PATCH [{n}] {label} (no rebuild)")
                t_before = time.time()
                try:
                    success = _dispatch_feature(n)
                except Exception as e:
                    err(str(e))
                    success = False
                dt = time.time() - t_before
                if success:
                    ok_count += 1
                    step_labels.append(label)
                    step_detail.append(f"{global_step}. {label} (session {dt:.1f}s) ✓")
                    ok(f"✓ {label} ({dt:.1f}s) — build ditunda")
                else:
                    fail_count += 1
                    batch_ok = False
                    step_detail.append(f"{global_step}. {label} ({dt:.1f}s) ✗")
                    cont = input(f"  {C.YELLOW}Lanjut batch? [Y/n]{C.RESET} ➤ ").strip().lower()
                    if cont in ("n", "no", "tidak"):
                        break

            # BUILD sekali
            out_name = mmk_output("app", os.path.splitext(os.path.basename(current_apk))[0] + "-batch.apk")
            built = mmk_session_finish(out_name=out_name)
            if built and os.path.isfile(built):
                old_input = os.path.abspath(current_apk)
                current_apk = os.path.abspath(built)
                MMK_PRESELECTED_APK = current_apk
                ok(f"Batch build: {os.path.basename(current_apk)} ({time.time()-t_batch:.1f}s)")
                if old_input != original_apk and old_input != current_apk:
                    _safe_remove_apk(old_input, protect_original=original_apk)
                prev_output = current_apk
            else:
                warn("Batch build gagal — APK tidak berubah")
                if mmk_session_active():
                    mmk_session_abort()
            print()
    finally:
        if mmk_session_active():
            mmk_session_abort()
        MMK_PRESELECTED_APK = None

    # ── RINGKASAN AKHIR ──
    elapsed_total = time.time() - t_run_start
    elapsed_str = f"{elapsed_total:.1f}s"
    if elapsed_total >= 60:
        elapsed_str = f"{int(elapsed_total // 60)}m {elapsed_total % 60:.0f}s"

    final_apk = current_apk if current_apk and os.path.isfile(current_apk) else original_apk
    app_name = os.path.basename(final_apk) if final_apk else "-"
    try:
        size_str = human_size(os.path.getsize(final_apk)) if final_apk and os.path.isfile(final_apk) else "-"
    except Exception:
        size_str = "-"
    sign_st = _apk_sign_status(final_apk)

    print()
    print(f"  {C.MAGENTA}╔{'═'*50}╗{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}{C.BOLD}{C.GREEN}{'MULTIBYPASS SELESAI'.center(50)}{C.RESET}{C.MAGENTA}║{C.RESET}")
    print(f"  {C.MAGENTA}╠{'═'*50}╣{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  {C.BOLD}Nama app    :{C.RESET} {C.CYAN}{app_name}{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  {C.BOLD}Size        :{C.RESET} {size_str}")
    print(f"  {C.MAGENTA}║{C.RESET}  {C.BOLD}Status sign :{C.RESET} {sign_st}")
    print(f"  {C.MAGENTA}║{C.RESET}  {C.BOLD}Durasi      :{C.RESET} {elapsed_str}")
    print(f"  {C.MAGENTA}║{C.RESET}  OK / Fail  : {ok_count}/{total}  (gagal {fail_count})")
    print(f"  {C.MAGENTA}╚{'═'*50}╝{C.RESET}")

    from datetime import datetime as _dt
    _mmk_history_save({
        "time": _dt.now().strftime("%Y-%m-%d %H:%M:%S"),
        "app_name": app_name,
        "size": size_str,
        "sign_status": sign_st,
        "elapsed": elapsed_str,
        "steps": " → ".join(step_labels) if step_labels else ",".join(seq),
        "steps_detail": step_detail,
        "modified": step_detail,
        "patches": patches_found,
        "ok": ok_count,
        "fail": fail_count,
        "total": total,
        "path": final_apk or "",
    })
    info("History disimpan — lihat menu 11")




# PairIP smali patterns (global — dipakai pairip_bypass_main)
# Search connectToLicensingService / onServiceConnected → return-void
PAIRIP_SMALI_PATTERNS = [
    (
        re.compile(
            r'\.method\s+(?:(private|public|protected)\s+)?connectToLicensingService\(\)V[\s\S]*?\.end\s+method',
            re.IGNORECASE,
        ),
        (
            ".method private connectToLicensingService()V\n"
            "    .registers 2\n\n"
            "    return-void\n"
            ".end method"
        ),
        "connectToLicensingService→return-void",
    ),
    (
        # no-arg + with params (ComponentName, IBinder)
        re.compile(
            r'\.method\s+(?:(private|public|protected)\s+)?onServiceConnected\([^\)]*\)V[\s\S]*?\.end\s+method',
            re.IGNORECASE,
        ),
        None,  # di-handle callback di pairip_bypass_main (pertahankan signature)
        "onServiceConnected→return-void",
    ),
]


def _pairip_patch_manifest(manifest_path):
    """Hapus CHECK_LICENSE + LicenseActivity dari satu file manifest. Return True jika berubah."""
    if not manifest_path or not os.path.isfile(manifest_path):
        return False
    try:
        with open(manifest_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return False
    original = content
    content, _ = re.subn(
        r'\s*<uses-permission[^>]*android:name\s*=\s*["\']com\.android\.vending\.CHECK_LICENSE["\'][^>]*/>\s*',
        "\n",
        content,
        flags=re.IGNORECASE,
    )
    content, _ = re.subn(
        r'\s*<uses-permission[^>]*com\.android\.vending\.CHECK_LICENSE[^>]*/?>\s*',
        "\n",
        content,
        flags=re.IGNORECASE,
    )
    content, _ = re.subn(
        r'\s*<activity[^>]*android:name\s*=\s*["\']com\.pairip\.licensecheck\.LicenseActivity["\'][\s\S]*?(?:/>|</activity>)\s*',
        "\n",
        content,
        flags=re.IGNORECASE,
    )
    content, _ = re.subn(
        r'\s*<activity[^>]*com\.pairip\.licensecheck\.[^"\']+["\'][\s\S]*?(?:/>|</activity>)\s*',
        "\n",
        content,
        flags=re.IGNORECASE,
    )
    if content != original:
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def _pairip_patch_smali_folder(dec):
    """Patch PairIP methods + manifest di folder decompile. Return (smali_files_changed, manifest_changed)."""
    roots = []
    for name in os.listdir(dec):
        p = os.path.join(dec, name)
        if os.path.isdir(p) and (name == "smali" or name.startswith("smali_")):
            roots.append(p)
    if not roots:
        roots = [dec]
    smali_files = []
    for base_r in roots:
        for root, _, fs in os.walk(base_r):
            for fn in fs:
                if fn.endswith(".smali"):
                    smali_files.append(os.path.join(root, fn))
    ok(f"{len(smali_files)} smali files")
    pat_license = PAIRIP_SMALI_PATTERNS[0][0]
    repl_license = PAIRIP_SMALI_PATTERNS[0][1]
    pat_onsvc = PAIRIP_SMALI_PATTERNS[1][0]

    def _on_svc(m):
        line0 = m.group(0).split("\n", 1)[0].rstrip()
        return (
            f"{line0}\n"
            "    .locals 0\n\n"
            "    return-void\n"
            ".end method"
        )

    changed = 0
    for i, fp in enumerate(smali_files, 1):
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue
        original = content
        content, n1 = pat_license.subn(repl_license, content)
        content, n2 = pat_onsvc.subn(_on_svc, content)
        if content != original:
            try:
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(content)
                changed += 1
                if changed <= 15 or changed % 50 == 0:
                    print(f"  {C.GREEN}✓{C.RESET} {os.path.relpath(fp, dec)}  {C.DIM}L={n1} S={n2}{C.RESET}")
            except Exception as e:
                warn(f"Write {os.path.basename(fp)}: {e}")
        if i % 300 == 0 or i == len(smali_files):
            progress_bar(i, len(smali_files), "pairip")
    ok(f"Smali patched: {changed} files")
    mc = 0
    try:
        mc = _smali_patch_pairip_manifest(dec) or 0
    except Exception:
        pass
    return changed, mc


def pairip_bypass_main():
    """Bypass PairIP license check — smali + AndroidManifest (MMK MOD)"""
    banner("PAIRIP BYPASS", "MMK MOD  •  license service + manifest")
    info("Credit: MMK MOD")
    print()
    info("Smali: connectToLicensingService / onServiceConnected → return-void")
    info("Manifest: hapus CHECK_LICENSE + LicenseActivity")
    print()

    # ── Session: patch only ──
    if mmk_session_active():
        dec = MMK_SESSION["dec"]
        mmk_session_print_bar()
        banner("PAIRIP (SESSION)", "patch only · build ditunda")
        changed, mc = _pairip_patch_smali_folder(dec)
        mmk_session_log("pairip")
        ok(f"PairIP done · smali={changed} manifest={mc} · ⏸ build ditunda")
        return

    if not shutil.which("java"):
        err("Java diperlukan")
        return

    jar = None
    try:
        jar = _smali_ensure_apkeditor()
    except Exception:
        pass
    if not jar:
        for f in os.listdir("."):
            if f.lower().endswith(".jar") and "apkeditor" in f.lower():
                jar = f
                break
    if not jar:
        err("APKEditor.jar tidak ditemukan")
        return
    jar_abs = os.path.abspath(jar)

    entries = mmk_list_apks()
    if not entries:
        err(f"Tidak ada APK di {MMK_APP_DIR}")
        return
    if "select_target" in globals():
        chosen = select_target(entries, title="SELECT TARGET  •  PAIRIP APK")
        if not chosen:
            return
        apk_path = chosen
    else:
        apk_path = os.path.abspath(apks[0])

    ok(f"Target: {os.path.basename(apk_path)}")
    work = os.getcwd()

    if apk_path.lower().endswith((".apks", ".xapk")):
        banner("MERGE", "APKS → APK dulu")
        merged = os.path.splitext(apk_path)[0] + "_merged.apk"
        rc = run_java_quiet(["java", "-jar", jar_abs, "m", "-i", apk_path, "-o", merged, "-f"], label="MERGE")
        if rc != 0 or not os.path.exists(merged):
            err("Merge gagal")
            return
        apk_path = merged
        ok(f"Merged: {os.path.basename(apk_path)}")

    base = os.path.splitext(os.path.basename(apk_path))[0]
    dec = os.path.join(work, f"{base}_pairip_dec")
    out_apk = os.path.join(work, f"{base}-pairip-bypassed.apk")
    if os.path.isdir(dec):
        shutil.rmtree(dec, ignore_errors=True)

    banner("DECOMPILE", "APKEditor")
    box_cmd_short("decompile", apk_path, dec, "pairip")
    rc = run_java_quiet(["java", "-jar", jar_abs, "d", "-i", apk_path, "-o", dec, "-f"], label="DECOMPILE")
    if rc != 0 or not os.path.isdir(dec):
        err("Decompile gagal")
        return
    ok("Decompiled")

    banner("PATCH", "PairIP smali + manifest")
    changed, mc = _pairip_patch_smali_folder(dec)

    banner("BUILD", "APKEditor b")
    out_apk = mmk_output("patched", os.path.basename(out_apk))
    if os.path.exists(out_apk):
        try:
            os.remove(out_apk)
        except Exception:
            pass
    box_cmd_short("build", dec, out_apk, "pairip")
    rc = run_java_quiet(["java", "-jar", jar_abs, "b", "-i", dec, "-o", out_apk, "-f"], label="BUILD")
    if rc != 0 or not os.path.exists(out_apk):
        err("Build gagal")
        return

    ans = input(f"  {C.YELLOW}Hapus decompile? [y/N]{C.RESET} ➤ ").strip().lower()
    if ans in ("y", "ya", "yes", "1"):
        shutil.rmtree(dec, ignore_errors=True)

    print()
    print(f"  {C.MAGENTA}╔{'═'*50}╗{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}{C.BOLD}{C.GREEN}{'PAIRIP BYPASS DONE — MMK MOD'.center(50)}{C.RESET}{C.MAGENTA}║{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  Output : {C.CYAN}{os.path.basename(out_apk)}{C.RESET}")
    print(f"  {C.MAGENTA}║{C.RESET}  Smali  : {changed} files · manifest={mc}")
    print(f"  {C.MAGENTA}╚{'═'*50}╝{C.RESET}")
    info("Sign APK (menu 6) sebelum install")




# ═══════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════
#  SECTION: ADS REGEX + EXTRA PATCHES
#  Pola publik setara Ads-Regex community (loadAd/showAd/analytics)
#  + FLAG_SECURE / black screen + lazy unlock style
#  Ref: github.com/ramanveerji/Ads-Regex-Official (app; regex offline)
# ═══════════════════════════════════════════════════════════════

# (pattern, replacement, label)
# replacement: special tokens __RETURN_VOID__ __RETURN_FALSE__ __RETURN_TRUE__ __COMMENT__
# ── REGEX PRO catalogs (numbered per category) ─────────────────
# Format item: (compiled_re, replacement, short_label)

REGEX_PRO_ADS = [
    (
        re.compile(
            r"(\.method\s+(?:public|private|static)\s+(?!\babstract\b|\bnative\b)[^\n]*\bloadAd\s*\([^)]*\)V\s*\n)([\s\S]*?)(\n\.end method)",
            re.I,
        ),
        "__RETURN_VOID__",
        "loadAd()V → return-void",
    ),
    (
        re.compile(
            r"(\.method\s+(?:public|private|static)\s+(?!\babstract\b|\bnative\b)[^\n]*\bloadAd\s*\([^)]*\)Z\s*\n)([\s\S]*?)(\n\.end method)",
            re.I,
        ),
        "__RETURN_FALSE__",
        "loadAd()Z → false",
    ),
    (
        re.compile(
            r"^([ \t]*)(invoke-\S+[^\n]*\bloadAd\s*\([^)]*\)[VZ][^\n]*)$",
            re.I | re.M,
        ),
        r"\1#\2",
        "comment invoke loadAd",
    ),
    (
        re.compile(
            r"(\.method[^\n]*(?:loadAd|requestNativeAd|showInterstitial|fetchad|fetchads|onadloaded|requestInterstitialAd|showAd|loadAds|AdRequest|requestBannerAd|loadNextAd|createInterstitialAd|setNativeAd|loadBannerAd|loadNativeAd|loadRewardedAd|loadRewardedInterstitialAd|loadAdViewAd|showInterstitialAd|shownativead|showbannerad|showvideoad|onAdFailedToLoad)\s*\([^)]*\)V\s*\n[ \t]*\.registers\s+\d+)([\s\S]*?)(\n\.end method)",
            re.I,
        ),
        "__RETURN_VOID__",
        "ad methods ()V → void",
    ),
    (
        re.compile(
            r"(\.method\s+(?:public|private|static)\s+(?!\babstract\b|\bnative\b)[^\n]*(?:loadAd|renderAd|Ad(?:Clicked|Dismissed|Shown))\s*\([^)]*\)V\s*\n[ \t]*\.registers\s+\d+)([\s\S]*?)(\n\.end method)",
            re.I,
        ),
        "__RETURN_VOID__",
        "loadAd/renderAd/Ad* ()V → void",
    ),
    (
        re.compile(
            r"^([ \t]*)(invoke-\S+[^\n]*(?:loadAd|requestNativeAd|showInterstitial|fetchAd|fetchAds|showAd|loadAds|requestBannerAd|loadRewarded|showInterstitialAd|showBanner|showVideo|AdListener)[^\n]*)$",
            re.I | re.M,
        ),
        r"\1#\2",
        "comment invoke ad-API",
    ),
    (
        re.compile(r"ca-app-pub-\d{16}/\d{10}"),
        "ca-app-pub-0000000000000000/0000000000",
        "null AdMob unit id",
    ),
]

# keep alias for old code paths
ADS_REGEX_PATTERNS = REGEX_PRO_ADS

REGEX_PRO_LAZY = [
    (
        re.compile(
            r"([ \t]*const-string\s+[vp]\d+,\s*\"(?:get|has|is)?[_\s-]?(?:pro|vip|premium|owned|purchased?|paid|iap|iab|subs|subscribed|full|noads?|donated|unlocked|adfree|sku|onetime|lifetime|plus)[\s_-]?(?:version|member|unlocked|subs|user)?\"\s*\n(?:\s*\n[ \t]*const/4\s+[vp]\d+,\s*0x[01])?\s*\n[ \t]*invoke[^\n]*;->getBoolean[^\n]*\)Z\s*\n[ \t]*)move-result\s+([vp]\d+)",
            re.I,
        ),
        r"\1const/4 \2, 0x1",
        "getBoolean premium key → true",
    ),
    (
        re.compile(
            r"([ias]get-boolean\s+([vp]\d+)[^\n]*;->(?:has|is|get)?(?:paid|pro|vip|premium|purchased|gold|subs|subscription|subscribed|owned)(?:user|version|member|status)?\s*:\s*Z)",
            re.I,
        ),
        r"const/4 \2, 0x1",
        "iget-boolean premium → true",
    ),
    (
        re.compile(
            r"(\.method\s+(.+)\s+((?:has|is|get_?(?:is)?)(?:pro|vip|premium|owned|purchased?|paid|iap|iab|subs|subscribed|noads|donated|unlocked|adfree|sku|onetime|lifetime|plus|PurchaseFlag)|allowEmojisForNonPremium|isAdsDisabled|isPremiumUser)\s*\(([^)]*)\)Z\s*\n[ \t]*\.registers\s+(\d+)\s*\n)([\s\S]*?)(\n\.end method)",
            re.I,
        ),
        "__RETURN_TRUE__",
        "method isPremium/isPro → true",
    ),
    (
        re.compile(
            r"([ \t]*invoke-[^\n]*;->[^\n]*(?:Premium|RemoveAds|Pro|Vip|Paid|Purchased|Subscri|gold|Gold|premium|vip|IsSubscription|isSubscription|proVersion|ProVersion|isProVersion)[^\n]*\)Z\s*\n[ \t]*move-result\s+([pv]\d+))",
            re.I,
        ),
        r"    const/4 \2, 0x1",
        "invoke+move-result premium → true",
    ),
    (
        re.compile(
            r"([ias]get-boolean\s+([pv]\d+)[^\n]*;->[^\n]*(?:Premium|RemoveAds|Pro|Vip|Paid|Purchased|Subscri|gold|Gold|premium|vip|proVersion|ProVersion)\s*:\s*Z)",
            re.I,
        ),
        r"const/4 \2, 0x1",
        "field premium boolean → true",
    ),
]

LAZY_UNLOCK_PATTERNS = REGEX_PRO_LAZY

REGEX_PRO_ANTISS = [
    # User request: Window Flags + const/16 x, 0x2000 → 0x0
    (
        re.compile(
            r"(const/16\s+([vp]\d+)\s*,\s*)0x2000\b",
            re.I,
        ),
        r"\g<1>0x0",
        "const/16 *, 0x2000 → 0x0",
    ),
    (
        re.compile(
            r"(const(?:/16|/high16)?\s+([vp]\d+)\s*,\s*)0x2000\b",
            re.I,
        ),
        r"\g<1>0x0",
        "const* *, 0x2000 → 0x0",
    ),
    (
        re.compile(
            r"^([ \t]*)(invoke-virtual\s+\{[^}]+\},\s*Landroid/view/Window;->(?:setFlags|addFlags)\(I(?:I)?\)V\s*)$",
            re.I | re.M,
        ),
        r"\1#\2",
        "comment Window.setFlags/addFlags",
    ),
]

FLAG_SECURE_PATTERNS = REGEX_PRO_ANTISS

ANALYTICS_PATTERNS = [
    (
        re.compile(
            r"(\.method\s+[^\n]*\b(logEvent|logPurchase|setUserProperty|trackEvent|sendEvent)\s*\([^)]*\)V\s*\n)([\s\S]*?)(\n\.end method)",
            re.I,
        ),
        "__RETURN_VOID__",
        "analytics log* → void",
    ),
]


def _ads_apply_repl(head, body_end, kind):
    if kind == "__RETURN_VOID__":
        return head + "    .locals 0\n\n    return-void\n" + body_end
    if kind == "__RETURN_FALSE__":
        return head + "    .locals 1\n\n    const/4 v0, 0x0\n\n    return v0\n" + body_end
    if kind == "__RETURN_TRUE__":
        return head + "    .locals 1\n\n    const/4 v0, 0x1\n\n    return v0\n" + body_end
    return head + body_end


def _ads_patch_content(content, patterns):
    hits = {}
    for item in patterns:
        if len(item) != 3:
            continue
        rx, repl, label = item
        n = 0
        if callable(repl):
            content, n = rx.subn(repl, content)
        elif isinstance(repl, str) and repl.startswith("__RETURN_"):
            def _sub(m, _repl=repl):
                if m.lastindex and m.lastindex >= 3:
                    head = m.group(1)
                    end = m.group(m.lastindex)
                    return _ads_apply_repl(head, end, _repl)
                return m.group(0)
            content, n = rx.subn(_sub, content)
        else:
            content, n = rx.subn(repl, content)
        if n:
            hits[label] = hits.get(label, 0) + n
    return content, hits


def _ads_walk_smali(dec_dir, pattern_sets):
    smali_files = []
    for root, _, fs in os.walk(dec_dir):
        for fn in fs:
            if fn.endswith(".smali"):
                smali_files.append(os.path.join(root, fn))
    ok(f"{len(smali_files)} smali files")
    changed_files = 0
    summary = {}
    for i, fp in enumerate(smali_files, 1):
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue
        original = content
        file_hits = {}
        for pats in pattern_sets:
            content, hits = _ads_patch_content(content, pats)
            for k, v in hits.items():
                file_hits[k] = file_hits.get(k, 0) + v
                summary[k] = summary.get(k, 0) + v
        if content != original:
            try:
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(content)
                changed_files += 1
                if changed_files <= 12 or changed_files % 40 == 0:
                    print(f"  {C.GREEN}✓{C.RESET} {os.path.relpath(fp, dec_dir)}  {C.DIM}{file_hits}{C.RESET}")
            except Exception as e:
                warn(f"Write {os.path.basename(fp)}: {e}")
        if i % 250 == 0 or i == len(smali_files):
            progress_bar(i, len(smali_files), "regex pro")
    return changed_files, summary


def _ads_run_pipeline(apk_path, pattern_sets, tag="regexpro"):
    """Decompile → patch → build. Session = patch only."""
    if mmk_session_active():
        dec = MMK_SESSION["dec"]
        mmk_session_print_bar()
        banner("REGEX PRO (SESSION)", tag)
        n, summary = _ads_walk_smali(dec, pattern_sets)
        mmk_session_log(f"regex:{tag}")
        ok(f"Files changed: {n}")
        for k, v in summary.items():
            print(f"  {C.CYAN}•{C.RESET} {k}: {v}")
        ok("⏸ build ditunda (session / multibypass)")
        return None

    if not shutil.which("java"):
        err("Java diperlukan")
        return None
    jar = None
    try:
        jar = _find_or_fetch_apkeditor()
    except Exception:
        pass
    if not jar:
        try:
            jar = _smali_ensure_apkeditor()
        except Exception:
            pass
    if not jar:
        err("APKEditor.jar tidak ditemukan")
        return None
    jar_abs = os.path.abspath(jar)
    apk_path = os.path.abspath(apk_path)
    if apk_path.lower().endswith((".apks", ".xapk")):
        merged = os.path.splitext(apk_path)[0] + "_merged.apk"
        run_java_quiet(["java", "-jar", jar_abs, "m", "-i", apk_path, "-o", merged, "-f"], label="MERGE")
        if os.path.isfile(merged):
            apk_path = merged

    base = os.path.splitext(os.path.basename(apk_path))[0]
    dec = os.path.abspath(f"_{tag}_{base}_dec")
    out_apk = mmk_output("patched", f"{base}-{tag}.apk")
    if os.path.isdir(dec):
        shutil.rmtree(dec, ignore_errors=True)
    banner("DECOMPILE", "APKEditor d")
    spinner("Decompile...", 1.0)
    rc = run_java_quiet(["java", "-jar", jar_abs, "d", "-i", apk_path, "-o", dec, "-f"], label="DECOMPILE")
    if rc != 0 or not os.path.isdir(dec):
        err("Decompile gagal")
        return None
    banner("PATCH", tag)
    n, summary = _ads_walk_smali(dec, pattern_sets)
    ok(f"Files changed: {n}")
    for k, v in sorted(summary.items(), key=lambda x: -x[1]):
        print(f"  {C.CYAN}•{C.RESET} {k}: {v}")
    if n == 0:
        warn("Tidak ada match")
    banner("BUILD", "APKEditor b")
    if os.path.exists(out_apk):
        try:
            os.remove(out_apk)
        except Exception:
            pass
    spinner("Build...", 1.2)
    run_java_quiet(["java", "-jar", jar_abs, "b", "-i", dec, "-o", out_apk, "-f"], label="BUILD")
    if not os.path.isfile(out_apk):
        run_java_quiet(["java", "-jar", jar_abs, "b", "-i", dec, "-o", out_apk, "-f"], label="BUILD")
    shutil.rmtree(dec, ignore_errors=True)
    if not os.path.isfile(out_apk):
        err("Build gagal")
        return None
    ok(f"Output: {os.path.basename(out_apk)}")
    return out_apk


def _regex_pro_pick_indices(patterns, title):
    """Tampilkan list nomor + minta input 1,5,3."""
    print()
    print(f"  {C.BOLD}{C.CYAN}{title}{C.RESET}")
    print(f"  {C.DIM}{'─'*56}{C.RESET}")
    for i, (_, _, lab) in enumerate(patterns, 1):
        print(f"  {C.GREEN}{i:>2}){C.RESET}  {lab}")
    print(f"  {C.DIM}{'─'*56}{C.RESET}")
    print(f"  {C.DIM}Contoh: 1,3,5  atau  all{C.RESET}")
    raw = input(f"  {C.MAGENTA}Pilih nomor ➤{C.RESET} ").strip().lower()
    if not raw:
        return []
    if raw in ("all", "a", "*"):
        return list(patterns)
    parts = re.split(r"[,;\s]+", raw)
    chosen = []
    for p in parts:
        if not p.isdigit():
            continue
        idx = int(p)
        if 1 <= idx <= len(patterns):
            chosen.append(patterns[idx - 1])
    return chosen


def ads_regex_main():
    """REGEX PRO — Ads / Patch Lazy / Anti-SS dengan pilih nomor regex."""
    banner("REGEX PRO", "MMK MOD  ·  Ads · Lazy · Anti screenshot")
    info("Credit: MMK MOD")
    print()
    print(f"  {C.GREEN}1){C.RESET}  Ads regex           {C.DIM}loadAd / showAd / AdMob{C.RESET}")
    print(f"  {C.GREEN}2){C.RESET}  Patch Lazy          {C.DIM}premium / pro / vip → true{C.RESET}")
    print(f"  {C.GREEN}3){C.RESET}  Bypass Anti-SS      {C.DIM}FLAG_SECURE 0x2000 → 0x0{C.RESET}")
    print(f"  {C.GREEN}4){C.RESET}  ALL (1+2+3)         {C.DIM}pilih nomor di tiap kategori{C.RESET}")
    print(f"  {C.RED}0){C.RESET}  Kembali")
    print()
    c = input(f"  {C.MAGENTA}➤{C.RESET} ").strip()
    if c == "0" or not c:
        return

    selected = []
    tag_parts = []
    if c == "1":
        picked = _regex_pro_pick_indices(REGEX_PRO_ADS, "ADS REGEX")
        if not picked:
            info("Dibatalkan")
            return
        selected.append(picked)
        tag_parts.append("ads")
    elif c == "2":
        picked = _regex_pro_pick_indices(REGEX_PRO_LAZY, "PATCH LAZY")
        if not picked:
            info("Dibatalkan")
            return
        selected.append(picked)
        tag_parts.append("lazy")
    elif c == "3":
        picked = _regex_pro_pick_indices(REGEX_PRO_ANTISS, "ANTI-SS / FLAG_SECURE")
        if not picked:
            info("Dibatalkan")
            return
        selected.append(picked)
        tag_parts.append("antiss")
    elif c == "4":
        for name, catalog, short in (
            ("ADS REGEX", REGEX_PRO_ADS, "ads"),
            ("PATCH LAZY", REGEX_PRO_LAZY, "lazy"),
            ("ANTI-SS", REGEX_PRO_ANTISS, "antiss"),
        ):
            picked = _regex_pro_pick_indices(catalog, name)
            if picked:
                selected.append(picked)
                tag_parts.append(short)
        if not selected:
            info("Tidak ada regex dipilih")
            return
    else:
        warn("Pilihan tidak valid")
        return

    tag = "regexpro-" + "-".join(tag_parts)

    if mmk_session_active():
        apk_path = MMK_SESSION.get("apk")
        ok(f"Session APK: {os.path.basename(apk_path or '?')}")
    else:
        entries = mmk_list_apks()
        if not entries:
            err(f"Tidak ada APK di {MMK_APP_DIR}")
            return
        apk_path = select_target(entries, title="SELECT APK  ·  REGEX PRO") if "select_target" in globals() else os.path.abspath(apks[0])
        if not apk_path:
            return

    t0 = time.time()
    out = _ads_run_pipeline(apk_path, selected, tag=tag)
    dt = time.time() - t0
    if out and os.path.isfile(out):
        print()
        print(f"  {C.MAGENTA}╔{'═'*50}╗{C.RESET}")
        print(f"  {C.MAGENTA}║{C.RESET}{C.BOLD}{C.GREEN}{'REGEX PRO DONE'.center(50)}{C.RESET}{C.MAGENTA}║{C.RESET}")
        print(f"  {C.MAGENTA}║{C.RESET}  Output : {C.CYAN}{os.path.basename(out)}{C.RESET}")
        print(f"  {C.MAGENTA}║{C.RESET}  Time   : {dt:.1f}s")
        print(f"  {C.MAGENTA}╚{'═'*50}╝{C.RESET}")
        warn("Sign (menu 6) sebelum install")



def wa_bot_menu():
    """
    Launcher / panduan MMK WhatsApp Bot (Baileys).
    File bot: folder mmk_wa_bot/ (Node.js) — tidak jalan di NxCreate (Telegram-only).
    """
    banner("WHATSAPP BOT", "MMK MOD  ·  Baileys multi-device")
    info("Lib aman: https://github.com/WhiskeySockets/Baileys (MIT)")
    print()
    print(f"  {C.YELLOW}⚠ NxCreate = bot Telegram, BUKAN WhatsApp{C.RESET}")
    print(f"  {C.DIM}Jalankan bot WA di Node.js: VPS / PC / Termux{C.RESET}")
    print()
    print(f"  {C.GREEN}1){C.RESET}  Tampilkan cara install")
    print(f"  {C.GREEN}2){C.RESET}  Cek Node.js & folder bot")
    print(f"  {C.GREEN}3){C.RESET}  Jalankan npm start (jika folder ada)")
    print(f"  {C.RED}0){C.RESET}  Kembali")
    print()
    c = input(f"  {C.MAGENTA}➤{C.RESET} ").strip()
    if c == "0" or not c:
        return
    bot_dirs = [
        os.path.abspath("mmk_wa_bot"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else ".", "mmk_wa_bot"),
        os.path.join(str(Path.home()), "mmk_wa_bot"),
        "/storage/emulated/0/Zbot/mmk_wa_bot",
    ]
    bot_dir = next((d for d in bot_dirs if os.path.isdir(d) and os.path.isfile(os.path.join(d, "index.js"))), None)

    if c == "1":
        print()
        print(f"  {C.BOLD}INSTALL{C.RESET}")
        print(f"  {C.DIM}1. Copy folder mmk_wa_bot ke server{C.RESET}")
        print(f"  {C.DIM}2. cd mmk_wa_bot && npm install && npm start{C.RESET}")
        print(f"  {C.DIM}3. Scan QR di terminal{C.RESET}")
        print()
        print(f"  {C.BOLD}Perintah bot{C.RESET}: !ping  !help  !info  !echo teks")
        print(f"  {C.BOLD}ENV{C.RESET}: MMK_WA_OWNER=62812...  MMK_WA_PREFIX=!")
        print()
        warn("Jangan spam — risiko ban WhatsApp")
        return

    if c == "2":
        node = shutil.which("node")
        npm = shutil.which("npm")
        info(f"node: {node or 'TIDAK ADA'}")
        info(f"npm : {npm or 'TIDAK ADA'}")
        info(f"bot : {bot_dir or 'folder mmk_wa_bot tidak ketemu'}")
        if not node:
            info("Termux: pkg install nodejs")
            info("Debian: apt install nodejs npm")
        return

    if c == "3":
        if not bot_dir:
            err("Folder mmk_wa_bot tidak ditemukan di cwd / ~/mmk_wa_bot / Zbot")
            info("Extract/copy folder mmk_wa_bot dulu")
            return
        if not shutil.which("node") or not shutil.which("npm"):
            err("Node.js / npm belum terpasang")
            return
        ok(f"Bot dir: {bot_dir}")
        node_modules = os.path.join(bot_dir, "node_modules")
        if not os.path.isdir(node_modules):
            banner("NPM INSTALL", "sekali saja")
            subprocess.call(["npm", "install"], cwd=bot_dir)
        banner("START BOT", "Ctrl+C untuk stop")
        warn("QR muncul di terminal — scan dengan WhatsApp")
        subprocess.call(["npm", "start"], cwd=bot_dir)
        return
    warn("Pilihan tidak valid")



#  SECTION: REVENGI-STYLE TOOLKIT (offline / local)
#  Inspired by feature matrix: https://github.com/RevEngiSquad
#  Implementasi lokal — tidak memanggil API RevEngi berbayar
# ═══════════════════════════════════════════════════════════════

_SMALI_GRAMMAR = {
    "invoke-virtual": ("35c", "invoke-virtual {params}, Ltype;->name(args)ret", "Panggil instance method virtual"),
    "invoke-super": ("35c", "invoke-super {params}, Ltype;->name(args)ret", "Panggil method superclass"),
    "invoke-direct": ("35c", "invoke-direct {params}, Ltype;->name(args)ret", "Panggil constructor / private"),
    "invoke-static": ("35c", "invoke-static {params}, Ltype;->name(args)ret", "Panggil static method"),
    "invoke-interface": ("35c", "invoke-interface {params}, Ltype;->name(args)ret", "Panggil interface method"),
    "const/4": ("11n", "const/4 vA, #+B", "Konstanta 4-bit (-8..7) ke register"),
    "const/16": ("21s", "const/16 vAA, #+BBBB", "Konstanta 16-bit"),
    "const": ("31i", "const vAA, #+BBBBBBBB", "Konstanta 32-bit"),
    "const-string": ("21c", "const-string vAA, string@BBBB", "Load string constant"),
    "move-result": ("11x", "move-result vAA", "Ambil hasil invoke (int/ref)"),
    "move-result-object": ("11x", "move-result-object vAA", "Ambil hasil object"),
    "return-void": ("10x", "return-void", "Return dari method void"),
    "return": ("11x", "return vAA", "Return nilai primitif"),
    "return-object": ("11x", "return-object vAA", "Return object"),
    "if-eqz": ("21t", "if-eqz vAA, +BBBB", "Branch jika == 0"),
    "if-nez": ("21t", "if-nez vAA, +BBBB", "Branch jika != 0"),
    "goto": ("10t", "goto +AA", "Jump tak bersyarat"),
    "new-instance": ("21c", "new-instance vAA, type@BBBB", "Alokasi object baru"),
    "check-cast": ("21c", "check-cast vAA, type@BBBB", "Cast tipe, throw jika gagal"),
    "iget": ("22c", "iget vA, vB, field", "Instance get field"),
    "iput": ("22c", "iput vA, vB, field", "Instance put field"),
    "sget": ("21c", "sget vAA, field", "Static get field"),
    "sput": ("21c", "sput vAA, field", "Static put field"),
}


def _rev_pick_file(exts, title="SELECT FILE"):
    files = []
    for f in sorted(os.listdir(".")):
        low = f.lower()
        if any(low.endswith(e) for e in exts) and os.path.isfile(f):
            try:
                files.append((os.path.abspath(f), f, os.path.getsize(f)))
            except OSError:
                pass
    if not files:
        err(f"Tidak ada file {exts} di folder")
        return None
    if "select_target" in globals():
        return select_target(files, title=title)
    return files[0][0]


def _rev_base_converter():
    banner("BASE CONVERTER", "hex · int · bin · bytes")
    s = input(f"  {C.CYAN}Input{C.RESET} (0x.. / decimal / bin 0b..) ➤ ").strip()
    if not s:
        return
    try:
        if s.lower().startswith("0x"):
            n = int(s, 16)
        elif s.lower().startswith("0b"):
            n = int(s, 2)
        else:
            n = int(s, 10)
    except Exception:
        b = s.encode("utf-8")
        print(f"  ASCII bytes : {b.hex()}")
        print(f"  len         : {len(b)}")
        return
    print(f"  {C.GREEN}dec{C.RESET}  {n}")
    print(f"  {C.GREEN}hex{C.RESET}  0x{n & 0xFFFFFFFFFFFFFFFF:X}")
    print(f"  {C.GREEN}bin{C.RESET}  {bin(n)}")
    if 0 <= n < 0x110000:
        try:
            print(f"  {C.GREEN}char{C.RESET} {chr(n)}")
        except Exception:
            pass
    le = (n & 0xFFFFFFFF).to_bytes(4, "little")
    be = (n & 0xFFFFFFFF).to_bytes(4, "big")
    print(f"  {C.GREEN}LE32{C.RESET} {le.hex()}")
    print(f"  {C.GREEN}BE32{C.RESET} {be.hex()}")


def _rev_smali_grammar():
    banner("SMALI GRAMMAR", "opcode reference")
    q = input(f"  {C.CYAN}Opcode / keyword{C.RESET} (kosong=list) ➤ ").strip().lower()
    if not q:
        for k, (fmt, syn, desc) in sorted(_SMALI_GRAMMAR.items()):
            print(f"  {C.CYAN}{k:<22}{C.RESET} [{fmt}] {C.DIM}{desc}{C.RESET}")
        return
    hits = [(k, v) for k, v in _SMALI_GRAMMAR.items() if q in k]
    if not hits and q in _SMALI_GRAMMAR:
        hits = [(q, _SMALI_GRAMMAR[q])]
    if not hits:
        warn("Tidak ketemu di database lokal (subset umum)")
        info("Referensi lengkap: dalvik bytecode / AOSP")
        return
    for k, (fmt, syn, desc) in hits:
        print(f"  {C.BOLD}{k}{C.RESET}")
        print(f"    format : {fmt}")
        print(f"    syntax : {syn}")
        print(f"    desc   : {desc}")


def _rev_smali_to_frida():
    banner("SMALI → FRIDA", "generate hook template")
    print(f"  {C.DIM}Contoh class: com.example.User{C.RESET}")
    cls = input(f"  {C.CYAN}Class{C.RESET} ➤ ").strip()
    method = input(f"  {C.CYAN}Method{C.RESET} ➤ ").strip() or "isPremium"
    if not cls:
        err("Class wajib")
        return
    lines = [
        "Java.perform(function () {",
        f'  var C = Java.use("{cls}");',
        f"  C.{method}.implementation = function () {{",
        f'    console.log("[MMK] {cls}.{method} hooked");',
        f"    var ret = this.{method}.apply(this, arguments);",
        '    console.log("  original => " + ret);',
        "    // return true;  // force boolean",
        "    return ret;",
        "  };",
        "});",
    ]
    script = "\n".join(lines)
    print()
    print(f"  {C.GREEN}// Frida script{C.RESET}")
    print(script)
    out = f"frida_{method}.js"
    with open(out, "w", encoding="utf-8") as f:
        f.write(script + "\n")
    ok(f"Saved: {out}")


def _rev_apk_analyzer():
    banner("APK ANALYZER", "package / perms / size")
    apk = _rev_pick_file((".apk", ".apks", ".xapk"), "SELECT APK")
    if not apk:
        return
    ok(f"Target: {os.path.basename(apk)}")
    aapt = shutil.which("aapt") or shutil.which("aapt2")
    if aapt:
        spinner("aapt dump badging...", 0.5)
        try:
            out = subprocess.check_output(
                [aapt, "dump", "badging", apk],
                stderr=subprocess.STDOUT, text=True, errors="ignore",
            )
            for line in out.splitlines()[:40]:
                if any(k in line for k in (
                    "package:", "sdkVersion", "application-label",
                    "uses-permission", "launchable",
                )):
                    print(f"  {line}")
        except Exception as e:
            warn(f"aapt: {e}")
    try:
        with zipfile.ZipFile(apk, "r") as z:
            names = z.namelist()
            dex = [n for n in names if n.endswith(".dex")]
            so = [n for n in names if n.endswith(".so")]
            print(f"  {C.CYAN}entries{C.RESET} {len(names)}")
            print(f"  {C.CYAN}dex{C.RESET}     {len(dex)}  {dex[:6]}")
            print(f"  {C.CYAN}native{C.RESET}  {len(so)} so")
            flutter = any("libapp.so" in n or "libflutter.so" in n for n in names)
            hermes = any("index.android.bundle" in n or "libhermes" in n for n in names)
            print(f"  {C.CYAN}flutter{C.RESET} {flutter}  {C.CYAN}hermes{C.RESET} {hermes}")
    except Exception as e:
        err(str(e))


def _rev_apkid():
    banner("APKiD", "packer / protector detect")
    apk = _rev_pick_file((".apk", ".dex"), "SELECT APK/DEX")
    if not apk:
        return
    if not shutil.which("apkid"):
        warn("apkid belum terpasang")
        info("pip install apkid   (butuh yara)")
        return
    spinner("apkid scan...", 0.8)
    subprocess.call(["apkid", apk])


def _rev_dex_tools():
    banner("DEX TOOLS", "dex → jar / jadx / list")
    print(f"  {C.GREEN}1){C.RESET}  dex2jar (d2j-dex2jar)")
    print(f"  {C.GREEN}2){C.RESET}  jadx decompile APK/DEX")
    print(f"  {C.GREEN}3){C.RESET}  List DEX di APK")
    c = input(f"  {C.MAGENTA}➤{C.RESET} ").strip()
    if c == "1":
        dex = _rev_pick_file((".dex", ".apk"), "SELECT DEX/APK")
        if not dex:
            return
        tool = shutil.which("d2j-dex2jar") or shutil.which("dex2jar")
        if not tool:
            err("d2j-dex2jar tidak ada di PATH")
            return
        out = os.path.splitext(os.path.basename(dex))[0] + "-dex2jar.jar"
        subprocess.call([tool, dex, "-o", out])
        if os.path.isfile(out):
            ok(out)
    elif c == "2":
        apk = _rev_pick_file((".apk", ".dex"), "SELECT")
        if not apk:
            return
        jadx = shutil.which("jadx")
        if not jadx:
            err("jadx tidak ada — install jadx dulu")
            return
        outd = os.path.splitext(os.path.basename(apk))[0] + "_jadx"
        spinner("jadx -d ...", 1.0)
        subprocess.call([jadx, "-d", outd, apk])
        ok(f"Output: {outd}")
    elif c == "3":
        apk = _rev_pick_file((".apk",), "SELECT APK")
        if not apk:
            return
        with zipfile.ZipFile(apk) as z:
            for n in z.namelist():
                if n.endswith(".dex"):
                    info_z = z.getinfo(n)
                    print(f"  {n}  {human_size(info_z.file_size)}")


def _rev_arm_converter():
    banner("ARM CONVERTER", "hex ↔ bytes · endian")
    s = input(f"  {C.CYAN}Hex{C.RESET} (contoh 1f 20 03 d5) ➤ ").strip()
    if not s:
        return
    hx = re.sub(r"[^0-9a-fA-F]", "", s)
    if len(hx) % 2:
        err("Panjang hex ganjil")
        return
    b = bytes.fromhex(hx)
    print(f"  bytes : {list(b)}")
    print(f"  len   : {len(b)}")
    if len(b) >= 4:
        import struct
        print(f"  u32 LE: 0x{struct.unpack('<I', b[:4])[0]:08X}")
        print(f"  u32 BE: 0x{struct.unpack('>I', b[:4])[0]:08X}")
    try:
        from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
        md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
        print(f"  {C.CYAN}capstone arm64:{C.RESET}")
        for i in md.disasm(b, 0x0):
            print(f"    0x{i.address:x}:\t{i.mnemonic}\t{i.op_str}")
    except Exception:
        info("Install capstone untuk disasm: pip install capstone")


def _rev_ssl_patch_hint():
    banner("SSL PATCH", "smali trust-all hint")
    info("Pola umum (cek manual di smali):")
    print("  # TrustManager checkServerTrusted -> return-void")
    print("  # HostnameVerifier verify -> const/4 v0, 0x1 / return v0")
    info("Atau gunakan Smali Patcher (menu 3) + regex custom")
    ans = input(f"  {C.CYAN}Buka Smali Patcher sekarang? [y/N]{C.RESET} ➤ ").strip().lower()
    if ans in ("y", "ya", "yes"):
        smali_main()


def _rev_mt_hook_gen():
    banner("MT HOOK GEN", "template MT / Frida")
    cls = input(f"  {C.CYAN}Class{C.RESET} ➤ ").strip() or "com.example.App"
    method = input(f"  {C.CYAN}Method{C.RESET} ➤ ").strip() or "isPremium"
    print()
    lines = [
        f"# MT/Frida Hook — {cls}.{method}",
        "Java.perform(() => {",
        f'  const C = Java.use("{cls}");',
        f"  C.{method}.implementation = function() {{",
        f'    console.log("hook {method}");',
        "    return true;",
        "  };",
        "});",
    ]
    tpl = "\n".join(lines)
    print(tpl)
    fn = f"mthook_{method}.js"
    with open(fn, "w", encoding="utf-8") as f:
        f.write(tpl + "\n")
    ok(f"Saved {fn}")


def _rev_regex_maker():
    banner("REGEX MAKER", "smali premium helper")
    print(f"  {C.GREEN}1){C.RESET}  Boolean method -> return true")
    print(f"  {C.GREEN}2){C.RESET}  Void method -> return-void")
    c = input(f"  {C.MAGENTA}➤{C.RESET} ").strip()
    kw = input(f"  {C.CYAN}Keyword method{C.RESET} [isPremium] ➤ ").strip() or "isPremium"
    if c == "2":
        pat = r"\.method.*" + kw + r"\(\)V[\s\S]*?\.end method"
        repl = ".method ... return-void"
    else:
        pat = (
            r"\.method (.+) (" + kw + r")\((.*)\)Z\n\s+\.registers (\d+)\n[\s\S]+?\.end method"
        )
        repl = (
            r".method $1 $2($3)Z\n    .registers $4\n\n"
            r"    const/4 v0, 0x1\n\n    return v0\n.end method"
        )
    print(f"  {C.CYAN}SEARCH{C.RESET}")
    print(f"  {pat}")
    print(f"  {C.CYAN}REPLACE{C.RESET}")
    print(f"  {repl}")


def _rev_jni_extract():
    banner("JNI EXTRACT", "nm / strings on .so")
    so = _rev_pick_file((".so",), "SELECT .so")
    if not so:
        return
    nm = shutil.which("nm") or shutil.which("llvm-nm")
    if nm:
        spinner("nm -D ...", 0.5)
        try:
            out = subprocess.check_output(
                [nm, "-D", so], stderr=subprocess.DEVNULL, text=True, errors="ignore"
            )
            jni = [ln for ln in out.splitlines() if "Java_" in ln or "JNI_OnLoad" in ln]
            for ln in jni[:40]:
                print(f"  {ln}")
            if not jni:
                warn("Tidak ada simbol Java_* (mungkin stripped)")
        except Exception as e:
            warn(str(e))
    else:
        warn("nm tidak ada")
    st = shutil.which("strings")
    if st:
        try:
            out = subprocess.check_output([st, so], text=True, errors="ignore")
            hits = [ln for ln in out.splitlines() if ln.startswith("Java_") or "JNI" in ln]
            print(f"  {C.CYAN}strings JNI-ish:{C.RESET} {len(hits)}")
            for ln in hits[:30]:
                print(f"  {ln}")
        except Exception:
            pass


def _rev_xml_decompile():
    banner("XML / MANIFEST", "via APKEditor")
    apk = _rev_pick_file((".apk",), "SELECT APK")
    if not apk:
        return
    jar = None
    try:
        jar = _find_or_fetch_apkeditor() if "_find_or_fetch_apkeditor" in globals() else None
    except Exception:
        pass
    if not jar:
        err("APKEditor.jar diperlukan")
        return
    out = os.path.splitext(os.path.basename(apk))[0] + "_xml_dec"
    spinner("APKEditor d ...", 1.0)
    run_java_quiet(["java", "-jar", jar, "d", "-i", apk, "-o", out, "-f"], label="DECOMPILE")
    man = os.path.join(out, "AndroidManifest.xml")
    if os.path.isfile(man):
        ok(f"Manifest: {man}")
        with open(man, "r", encoding="utf-8", errors="ignore") as f:
            print(f.read()[:2000])
    else:
        warn("Manifest tidak ketemu — cek folder " + out)


def revengi_toolkit_main():
    """
    Revengi-style reverse engineering toolkit (local offline).
    Feature matrix inspired by RevEngiSquad — implemented where Termux/PC allows.
    """
    while True:
        banner("REVENGI TOOLKIT", "MMK MOD  ·  offline RE suite")
        info("Credit: MMK MOD  |  inspired by RevEngi feature list")
        print()
        print(f"  {C.BOLD}{C.CYAN}▶ CONVERT / REF{C.RESET}")
        print(f"     {C.GREEN}1){C.RESET}  Base Converter")
        print(f"     {C.GREEN}2){C.RESET}  Smali Grammar")
        print(f"     {C.GREEN}3){C.RESET}  Smali → Frida template")
        print(f"     {C.GREEN}4){C.RESET}  ARM Converter")
        print(f"     {C.GREEN}5){C.RESET}  Regex Maker")
        print()
        print(f"  {C.BOLD}{C.CYAN}▶ APK / DEX{C.RESET}")
        print(f"     {C.GREEN}6){C.RESET}  APK Analyzer")
        print(f"     {C.GREEN}7){C.RESET}  APKiD")
        print(f"     {C.GREEN}8){C.RESET}  DEX tools (dex2jar / jadx)")
        print(f"     {C.GREEN}9){C.RESET}  XML / Manifest decompile")
        print(f"    {C.GREEN}10){C.RESET}  APKS → APK          {C.DIM}→ menu 9{C.RESET}")
        print()
        print(f"  {C.BOLD}{C.CYAN}▶ NATIVE / HOOK{C.RESET}")
        print(f"    {C.GREEN}11){C.RESET}  JNI Extractor (.so)")
        print(f"    {C.GREEN}12){C.RESET}  Generate MT/Frida Hook")
        print(f"    {C.GREEN}13){C.RESET}  SSL Patch hint")
        print(f"    {C.GREEN}14){C.RESET}  PairIP Bypass       {C.DIM}→ menu 10{C.RESET}")
        print(f"    {C.GREEN}15){C.RESET}  Blutter / Flutter   {C.DIM}→ menu 1 / 5{C.RESET}")
        print(f"    {C.GREEN}16){C.RESET}  Protect APK         {C.DIM}→ menu 7{C.RESET}")
        print(f"    {C.GREEN}17){C.RESET}  Sign APK            {C.DIM}→ menu 6{C.RESET}")
        print()
        print(f"     {C.RED}0){C.RESET}  Kembali")
        print()
        c = input(f"  {C.MAGENTA}➤{C.RESET} ").strip()
        if c == "0" or c == "":
            return
        try:
            if c == "1":
                _rev_base_converter()
            elif c == "2":
                _rev_smali_grammar()
            elif c == "3":
                _rev_smali_to_frida()
            elif c == "4":
                _rev_arm_converter()
            elif c == "5":
                _rev_regex_maker()
            elif c == "6":
                _rev_apk_analyzer()
            elif c == "7":
                _rev_apkid()
            elif c == "8":
                _rev_dex_tools()
            elif c == "9":
                _rev_xml_decompile()
            elif c == "10":
                apks_to_apk_main()
            elif c == "11":
                _rev_jni_extract()
            elif c == "12":
                _rev_mt_hook_gen()
            elif c == "13":
                _rev_ssl_patch_hint()
            elif c == "14":
                pairip_bypass_main()
            elif c == "15":
                print(f"  {C.GREEN}1){C.RESET} Flutter  {C.GREEN}2){C.RESET} Toolkit/Blutter")
                s = input("  ➤ ").strip()
                if s == "2":
                    toolkit_main()
                else:
                    flutter_main()
            elif c == "16":
                protect_apk_main()
            elif c == "17":
                sign_apk_main()
            else:
                warn("Pilihan tidak valid")
        except SystemExit:
            pass
        except KeyboardInterrupt:
            print()
            warn("Dibatalkan")
        except Exception as e:
            err(str(e))
            import traceback
            traceback.print_exc()
        input(f"\n{C.YELLOW}Press Enter...{C.RESET}")


if __name__ == "__main__":
    try:
        _mmk_main_menu()
    except KeyboardInterrupt:
        print("\nBye.")
        sys.exit(0)
