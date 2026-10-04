#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MMK File-Only Telegram Bot
- Hermes : index.android.bundle
- Flutter: libapp.so / zip (libapp.so + asm/)
- Smali  : zip berisi .smali
"""
import os
import re
import sys
import shutil
import zipfile
import tempfile
import logging
import asyncio
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ═══════════ CONFIG ═══════════
BOT_TOKEN = "8724738364:AAGFsy6RyvrK7KHTSyt9IVjBV7XutReVMpA"
WORK_ROOT = Path(os.getenv("MMK_WORK_DIR", tempfile.gettempdir())) / "mmk_file_bot"
MAX_MB = int(os.getenv("MMK_MAX_MB", "45"))  # limit Telegram bot API biasa ~50MB

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("mmk-bot")


# ═══════════ SMALI PATTERNS (dari v2.py) ═══════════
SMALI_PATTERNS = [
    (
        re.compile(
            r"(\.method private connectToLicensingService\(\)V\s*\n\s*\.(?:registers|locals) \d+\s*\n)"
        ),
        r"\1    return-void\n",
        "s1",
    ),
    (
        re.compile(
            r"(\.method\spublic\sinitializeLicenseCheck\(\)V)(?:\s*\n\s+.*)*?return-void\n\.end\smethod"
        ),
        r"\1\n.registers 1\nreturn-void\n.end method",
        "s2",
    ),
    (
        re.compile(
            r"([ias]get-boolean ([pv]\d+)(?!.*(show|display|enablePrepaidPlans)).*;->.*"
            r"(Premium.*|RemoveAds.*|Pro|ispro|Vip.*|Paid.*|Subscri.*|gold.*|subscri.*|"
            r"purchase.*|adremoved.*|vip.*|isplus|ProVersion.*|ispaid|purchased|fullversion|"
            r"unlocked|subscribed|member|adsfree|noads|platinum|enterprise|ultimate|professional):Z)"
        ),
        r"\1\n const/4 \2, 0x1",
        "s3",
    ),
    (
        re.compile(
            r"([ias]put-boolean ([pv]\d+)(?!.*(show|display|enablePrepaidPlans)).*;->.*"
            r"(Premium.*|RemoveAds.*|Pro|ispro|Vip.*|Paid.*|Subscri.*|gold.*|subscri.*|"
            r"purchase.*|adremoved.*|vip.*|isplus|ProVersion.*|ispaid|purchased|fullversion|"
            r"unlocked|subscribed|member|adsfree|noads|platinum|enterprise|ultimate|professional):Z)"
        ),
        r"const/4 \2, 0x1\n\n    \1",
        "s4",
    ),
    (
        re.compile(
            r'(?i)(const-string[^"]+"(?!(?:.*(?:Disable|Hide|Remove|Free|Basic|Expired|Block)))'
            r'(?:is|get|has)?(?:Premium.*|Pro\b|Purchased.*|_purchase|NoAds|has_active_p.*|no_ads|'
            r'Subscriber|Paid\b|vip\b|AdFree|ProVersion|proUser|Elite\b|SUBSCRIBED|AdsRemoved|'
            r'Upgraded|Subscribed.*|Subscription|lifetime|Unlocked.*)[^"]*"'
            r'(?:[\s\S]*?)getBoolean\(Ljava/lang/String;Z\)Z[\s\S]{0,50}?)move-result ([pv]\d+)'
        ),
        r"\1\n const/4 \2, 0x1",
        "s6",
    ),
]


# ═══════════ HERMES PATTERN (dari v2.py) ═══════════
HERMES_SEARCH = re.compile(
    r"GetById.*(Reg8:\d+), Reg8:\d+, UInt8:\d+, UInt16:\d+\n"
    r".*\'(?i:ispremium|ispro\b|issubscribed|ispurchased|ispaid|haspurchase|isbought|"
    r"hasaccess|isunlocked|isfullversion|isvip|islicensed|haslicense|isfree|istrial|"
    r"getispremium|getispro|getpremium|getpro|getsubscribed|getsubscription|getpurchased|"
    r"getpaid|getaccess|getunlocked|getfullversion|getvip|getlicensed|getfree|gettrial|"
    r"haspremium|haspro|hassubscribed|haspurchased|haspaid|hasbought|hasunlocked|"
    r"hasfullversion|hasvip|haslicensed|hasfree|hastrial|vip|isvip|hasvip|ispremium|"
    r"premium|pro\b|vip|is_vip|is_premium)\'"
)
HERMES_REPLACE = r"LoadConstTrue     \1\nLoadConstTrue     \1\nLoadConstTrue     \1\n"


# ═══════════ HELPERS ═══════════
def have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def run_cmd(cmd, cwd=None, timeout=1800):
    try:
        p = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as e:
        return 1, str(e)


async def send_doc(update: Update, path: str, caption: str = ""):
    with open(path, "rb") as f:
        await update.message.reply_document(
            document=f, filename=os.path.basename(path), caption=caption
        )


# ═══════════ SMALI PROCESSOR ═══════════
def patch_smali_zip(zip_path: str, out_zip: str):
    """Return (n_files_patched, n_hits, total_smali)"""
    work = Path(tempfile.mkdtemp(prefix="smali_"))
    try:
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(work)

        total = 0
        patched_files = 0
        total_hits = 0

        for root, _, files in os.walk(work):
            for fn in files:
                if not fn.endswith(".smali"):
                    continue
                total += 1
                fp = os.path.join(root, fn)
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except Exception:
                    continue
                original = content
                hits = 0
                for pat, repl, _label in SMALI_PATTERNS:
                    content, n = pat.subn(repl, content)
                    hits += n
                if content != original:
                    try:
                        with open(fp, "w", encoding="utf-8") as f:
                            f.write(content)
                        patched_files += 1
                        total_hits += hits
                    except Exception:
                        pass

        with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(work):
                for fn in files:
                    fp = os.path.join(root, fn)
                    arc = os.path.relpath(fp, work)
                    z.write(fp, arc)
        return patched_files, total_hits, total
    finally:
        shutil.rmtree(work, ignore_errors=True)


# ═══════════ HERMES PROCESSOR ═══════════
def patch_hermes_bundle(bundle_path: str, out_bundle: str):
    """Return (n_patched, err_or_None). n_patched=None artinya gagal total."""
    if not have("hbctool"):
        return None, "hbctool tidak tersedia. Install: pip install hbctool  (atau wheel dari Kirlif/HBC-Tool)"

    work = Path(tempfile.mkdtemp(prefix="hermes_"))
    try:
        disasm_dir = work / "disasm"
        rc, out = run_cmd(["hbctool", "disasm", bundle_path, str(disasm_dir)], cwd=str(work))
        if rc != 0 or not disasm_dir.exists():
            return None, f"Disassembly gagal: {out[:400]}"

        inst = disasm_dir / "instruction.hasm"
        if not inst.exists():
            return None, "instruction.hasm tidak ditemukan"

        with open(inst, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        n = len(list(HERMES_SEARCH.finditer(content)))
        if n == 0:
            return 0, "Tidak ada pola premium/vip ditemukan"

        new_content = HERMES_SEARCH.sub(HERMES_REPLACE, content)
        with open(inst, "w", encoding="utf-8") as f:
            f.write(new_content)

        rc, out = run_cmd(["hbctool", "asm", str(disasm_dir), out_bundle], cwd=str(work))
        if rc != 0 or not os.path.isfile(out_bundle):
            return n, f"Assembly gagal: {out[:400]}"

        return n, None
    finally:
        shutil.rmtree(work, ignore_errors=True)


# ═══════════ FLUTTER PROCESSOR ═══════════
def patch_flutter_zip(zip_path: str, out_zip: str):
    """
    Input: zip berisi libapp.so + (asm/ ATAU blutter installed).
    Output: zip berisi hasil patch (0x30 -> 0x20 pada add xN, x22).
    Return ((n_files_patched, n_patches), err_or_None).
    """
    work = Path(tempfile.mkdtemp(prefix="flutter_"))
    try:
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(work)

        # cari libapp.so
        libapp = None
        for root, _, files in os.walk(work):
            for fn in files:
                if fn == "libapp.so":
                    libapp = os.path.join(root, fn)
                    break
            if libapp:
                break
        if not libapp:
            return None, "libapp.so tidak ditemukan di dalam zip"

        # cari folder asm/
        asm_dir = None
        for root, dirs, _ in os.walk(work):
            for d in dirs:
                if d == "asm":
                    asm_dir = os.path.join(root, d)
                    break
            if asm_dir:
                break

        # kalau tidak ada asm/, coba jalankan blutter
        if not asm_dir:
            blutter = Path.home() / "blutter-termux"
            if not (blutter / "blutter.py").is_file():
                return None, (
                    "Folder asm/ tidak ada di zip dan blutter-termux tidak terinstall.\n"
                    "Solusi: jalankan blutter dulu lokal, lalu zip isi out_dir/ (asm/ + pp.txt) + libapp.so."
                )
            libapp_dir = os.path.dirname(libapp)
            out_dir = work / "blutter_out"
            rc, out = run_cmd(
                ["python3", "blutter.py", libapp_dir, str(out_dir)],
                cwd=str(blutter), timeout=3600,
            )
            asm_dir = out_dir / "asm"
            if not asm_dir.exists():
                return None, f"Blutter gagal: {out[:400]}"

        # patch semua .dart: add xN, x22, 0x30 -> add xN, x22, 0x20
        n_files = 0
        n_patches = 0
        rx = re.compile(r"(add\s+x\d+),\s*x22,\s*0x30")
        for root, _, files in os.walk(asm_dir):
            for fn in files:
                if not fn.endswith(".dart"):
                    continue
                fp = os.path.join(root, fn)
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except Exception:
                    continue
                new_content, cnt = rx.subn(r"\1, x22, 0x20", content)
                if cnt:
                    try:
                        with open(fp, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        n_files += 1
                        n_patches += cnt
                    except Exception:
                        pass

        # zip output
        with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(work):
                for fn in files:
                    fp = os.path.join(root, fn)
                    arc = os.path.relpath(fp, work)
                    z.write(fp, arc)

        return (n_files, n_patches), None
    finally:
        shutil.rmtree(work, ignore_errors=True)


# ═══════════ HANDLERS ═══════════
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *MMK File Bot*\n\n"
        "Kirim file ke chat ini, bot proses otomatis:\n"
        "• `index.android.bundle` → *Hermes patch*\n"
        "• `libapp.so` / `.zip` berisi `libapp.so` + `asm/` → *Flutter patch*\n"
        "• `.zip` berisi file `.smali` → *Smali patch*\n\n"
        "Perintah: /help · /status",
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Cara pakai:*\n"
        "1. Kirim file sebagai *dokumen* (bukan teks)\n"
        "2. Bot deteksi tipe otomatis\n"
        "3. Bot balas file hasil proses\n\n"
        "*Format input:*\n"
        "• Hermes → `index.android.bundle`\n"
        "• Flutter → ZIP berisi `libapp.so` + folder `asm/` (dari blutter) \n"
        "    atau `libapp.so` saja (butuh blutter-termux terinstall)\n"
        "• Smali → ZIP berisi file `.smali` (struktur bebas)\n\n"
        f"*Limit:* maks {MAX_MB} MB per file\n"
        "Satu file per pesan.",
        parse_mode="Markdown",
    )


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    tools = ["java", "python3", "hbctool", "r2", "zip"]
    lines = []
    for t in tools:
        lines.append(f"{'✅' if have(t) else '❌'} `{t}`")
    blutter_ok = (Path.home() / "blutter-termux" / "blutter.py").is_file()
    lines.append(f"{'✅' if blutter_ok else '❌'} `blutter-termux`")
    await update.message.reply_text(
        "*Tools terdeteksi:*\n" + "\n".join(lines),
        parse_mode="Markdown",
    )


async def handle_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc:
        return

    size = doc.file_size or 0
    if size > MAX_MB * 1024 * 1024:
        await update.message.reply_text(
            f"❌ File terlalu besar ({size // 1024 // 1024} MB). Maks {MAX_MB} MB."
        )
        return

    name = doc.file_name or "file"
    lower = name.lower()
    status = await update.message.reply_text(
        f"📥 Menerima `{name}` ({size // 1024} KB)…", parse_mode="Markdown"
    )

    job_dir = Path(tempfile.mkdtemp(prefix=f"mmkjob_{update.effective_user.id}_"))
    try:
        tg_file = await ctx.bot.get_file(doc.file_id)
        local = job_dir / name
        await tg_file.download_to_drive(str(local))

        # ── HERMES ───────────────────────────────────────────
        if lower.endswith(".bundle") or "index.android.bundle" in lower:
            await status.edit_text("⚙️ *Hermes patch* berjalan…", parse_mode="Markdown")
            out = str(job_dir / (Path(name).stem + "-patched.bundle"))
            n, err = await asyncio.to_thread(patch_hermes_bundle, str(local), out)
            if n is None:
                await status.edit_text(f"❌ {err}")
                return
            if n == 0:
                await status.edit_text(f"ℹ️ Tidak ada pola premium/vip ditemukan.\n{err or ''}")
                return
            await status.delete()
            await send_doc(update, out, f"✅ Hermes patch: {n} pattern → LoadConstTrue")
            return

        # ── FLUTTER (single .so) ─────────────────────────────
        if lower.endswith(".so") and "libapp" in lower:
            await status.edit_text(
                "ℹ️ Untuk mode Flutter, kirim *ZIP* berisi:\n"
                "• `libapp.so`\n"
                "• folder `asm/` (hasil blutter)\n\n"
                "Atau pastikan `blutter-termux` terinstall di server, lalu kirim ZIP berisi `libapp.so` saja.",
                parse_mode="Markdown",
            )
            return

        # ── ZIP (smali / flutter) ────────────────────────────
        if lower.endswith(".zip"):
            try:
                with zipfile.ZipFile(local) as z:
                    names = z.namelist()
            except Exception:
                await status.edit_text("❌ ZIP tidak valid / corrupt")
                return

            has_smali = any(n.endswith(".smali") for n in names)
            has_libapp = any(n.endswith("libapp.so") for n in names)
            has_asm = any(n.startswith("asm/") or "/asm/" in n for n in names)

            if has_smali:
                await status.edit_text("⚙️ *Smali patch* berjalan…", parse_mode="Markdown")
                out = str(job_dir / (Path(name).stem + "-smali-patched.zip"))
                n_files, n_hits, total = await asyncio.to_thread(
                    patch_smali_zip, str(local), out
                )
                if n_hits == 0:
                    await status.edit_text(
                        f"ℹ️ Tidak ada pola yang cocok ({total} file .smali dipindai)"
                    )
                    return
                await status.delete()
                await send_doc(
                    update, out,
                    f"✅ Smali: {n_files} file dipatch ({n_hits} hit dari {total} file)"
                )
                return

            if has_libapp or has_asm:
                await status.edit_text("⚙️ *Flutter patch* berjalan…", parse_mode="Markdown")
                out = str(job_dir / (Path(name).stem + "-flutter-patched.zip"))
                res, err = await asyncio.to_thread(patch_flutter_zip, str(local), out)
                if res is None:
                    await status.edit_text(f"❌ {err}")
                    return
                nf, npatch = res
                if npatch == 0:
                    await status.edit_text(
                        f"ℹ️ Tidak ada pola `add xN, x22, 0x30` ({nf} file .dart berubah)"
                    )
                    return
                await status.delete()
                await send_doc(
                    update, out,
                    f"✅ Flutter: {nf} file .dart, {npatch} patch (0x30 → 0x20)"
                )
                return

            await status.edit_text(
                "❌ ZIP tidak dikenali.\n"
                "Harus berisi file `.smali` (mode smali) atau `libapp.so`/`asm/` (mode flutter)."
            )
            return

        await status.edit_text(
            "❌ Tipe file tidak didukung.\n"
            "Kirim `*.bundle`, `*.so` (libapp), atau `*.zip`."
        )

    except Exception as e:
        logger.exception("handler error")
        try:
            await status.edit_text(f"❌ Error: {e}")
        except Exception:
            pass
    finally:
        shutil.rmtree(job_dir, ignore_errors=True)


async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Kirim file sebagai *dokumen* (bukan teks). Ketik /help.",
        parse_mode="Markdown",
    )


# ═══════════ MAIN ═══════════
def main():
    if not BOT_TOKEN:
        print("⚠️  Set BOT_TOKEN dulu:  export BOT_TOKEN='123:ABC'")
        sys.exit(1)
    WORK_ROOT.mkdir(parents=True, exist_ok=True)

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    logger.info("Bot berjalan…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()