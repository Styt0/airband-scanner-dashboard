#!/usr/bin/env python3
"""
Archive SDR transmissions from Pi to OneDrive.

Downloads:
  1. Full database backup (db.sqlite3 -> archive/db_YYYY-MM-DD.sqlite3)
  2. CSV export of all transcribed transmissions
  3. Audio files from the last N days (before disk_rotation deletes them)

Run manually or schedule via Windows Task Scheduler.

Usage:
    python archive_transmissions.py               # DB + CSV only (fast)
    python archive_transmissions.py --audio        # DB + CSV + audio files
    python archive_transmissions.py --audio --days 3  # audio from last 3 days only
"""

import argparse
import csv
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import paramiko
except ImportError:
    print("ERROR: paramiko not installed. Run: pip install paramiko")
    sys.exit(1)

# ── Configuration ─────────────────────────────────────────────────────────────
PI_HOST     = "100.120.23.59"       # Tailscale IP
PI_USER     = "root"
PI_PASS     = os.environ.get("SDR_PI_PASS")   # set env var, or leave unset for SSH key auth
PI_DB_PATH  = "/opt/sdr-hub/data/db.sqlite3"
PI_MEDIA    = "/opt/sdr-hub/data/public/media"

ARCHIVE_DIR = Path(r"C:\Users\Tom\OneDrive\Claude\projects\sdr-hub-v2\archive")


def connect_ssh():
    """Create SSH + SFTP connection to Pi."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    kwargs = {"timeout": 15}
    if PI_PASS:
        kwargs["password"] = PI_PASS
    client.connect(PI_HOST, username=PI_USER, **kwargs)
    sftp = client.open_sftp()
    return client, sftp


def download_db(sftp, archive_dir):
    """Download full database backup."""
    today = datetime.now().strftime("%Y-%m-%d")
    db_dir = archive_dir / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    dest = db_dir / f"db_{today}.sqlite3"

    # Skip if already archived today
    if dest.exists():
        print(f"  DB backup already exists: {dest.name}")
        return dest

    print(f"  Downloading database -> {dest.name} ...", end=" ", flush=True)
    sftp.get(PI_DB_PATH, str(dest))
    size_mb = dest.stat().st_size / (1024 * 1024)
    print(f"done ({size_mb:.1f} MB)")

    # Keep only last 7 daily backups
    backups = sorted(db_dir.glob("db_*.sqlite3"), reverse=True)
    for old in backups[7:]:
        old.unlink()
        print(f"  Purged old backup: {old.name}")

    return dest


def export_csv(db_path, archive_dir):
    """Export transcribed transmissions to CSV from downloaded DB."""
    csv_dir = archive_dir / "csv"
    csv_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    csv_path = csv_dir / f"transcripts_{today}.csv"

    if csv_path.exists():
        print(f"  CSV already exists: {csv_path.name}")
        return csv_path

    print(f"  Exporting transcripts -> {csv_path.name} ...", end=" ", flush=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT t.id AS tx_id,
               t.begin_date,
               t.end_date,
               ROUND((t.begin_frequency + t.end_frequency) / 2.0 / 1e6, 3) AS freq_mhz,
               t.data_file,
               tr.text,
               tr.model,
               tr.confidence,
               tr.error
        FROM sdr_transmission t
        LEFT JOIN sdr_transcript tr ON tr.transmission_id = t.id
        LEFT JOIN sdr_group g ON g.id = t.group_id
        WHERE g.modulation = 'AM'
        ORDER BY t.begin_date DESC
    """).fetchall()
    conn.close()

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["tx_id", "begin_date", "end_date", "freq_mhz",
                         "data_file", "text", "model", "confidence", "error"])
        for r in rows:
            writer.writerow([r["tx_id"], r["begin_date"], r["end_date"],
                             r["freq_mhz"], r["data_file"], r["text"],
                             r["model"], r["confidence"], r["error"]])

    print(f"done ({len(rows):,} rows)")

    # Keep only last 7 daily CSVs
    csvs = sorted(csv_dir.glob("transcripts_*.csv"), reverse=True)
    for old in csvs[7:]:
        old.unlink()
        print(f"  Purged old CSV: {old.name}")

    return csv_path


def download_audio(client, sftp, archive_dir, days=7):
    """Download audio files from last N days before rotation deletes them."""
    audio_dir = archive_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Get list of date-folders on Pi
    tx_base = f"{PI_MEDIA}/device_3/transmission"
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

    print(f"  Scanning audio folders (last {days} days, cutoff: {cutoff}) ...")
    stdin, stdout, stderr = client.exec_command(f"ls {tx_base}/")
    date_folders = sorted(stdout.read().decode().strip().split("\n"))

    total_files = 0
    total_bytes = 0
    skipped = 0

    for folder in date_folders:
        if folder < cutoff:
            continue

        local_folder = audio_dir / folder
        local_folder.mkdir(parents=True, exist_ok=True)

        # List files in this date folder
        stdin, stdout, stderr = client.exec_command(f"ls {tx_base}/{folder}/")
        files = stdout.read().decode().strip().split("\n")
        if not files or files == [""]:
            continue

        for fname in files:
            local_path = local_folder / fname
            if local_path.exists():
                skipped += 1
                continue

            remote_path = f"{tx_base}/{folder}/{fname}"
            try:
                sftp.get(remote_path, str(local_path))
                size = local_path.stat().st_size
                total_files += 1
                total_bytes += size
            except Exception as e:
                print(f"    WARN: Failed {fname}: {e}")

        print(f"    {folder}: {len(files)} files", end="")
        if skipped:
            print(f" ({skipped} already archived)", end="")
        print()
        skipped = 0

    mb = total_bytes / (1024 * 1024)
    print(f"  Audio download complete: {total_files} new files ({mb:.1f} MB)")
    return total_files


def main():
    parser = argparse.ArgumentParser(description="Archive SDR transmissions to OneDrive")
    parser.add_argument("--audio", action="store_true",
                        help="Also download audio .bin files (can be large)")
    parser.add_argument("--days", type=int, default=7,
                        help="Days of audio to archive (default: 7)")
    args = parser.parse_args()

    print("=" * 40)
    print("  SDR Archive -> OneDrive")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 40)
    print()

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    print("[1/3] Connecting to Pi ...")
    try:
        client, sftp = connect_ssh()
        print("  Connected via Tailscale")
    except Exception as e:
        print(f"  FAILED: {e}")
        print("  Make sure Tailscale is running and Pi is online.")
        sys.exit(1)

    print()
    print("[2/3] Database backup ...")
    db_path = download_db(sftp, ARCHIVE_DIR)

    print()
    print("[3/3] CSV export ...")
    export_csv(db_path, ARCHIVE_DIR)

    if args.audio:
        print()
        print("[BONUS] Audio file archive ...")
        download_audio(client, sftp, ARCHIVE_DIR, days=args.days)

    print()
    sftp.close()
    client.close()

    # Summary
    db_size = sum(f.stat().st_size for f in (ARCHIVE_DIR / "db").glob("*.sqlite3")) / (1024*1024)
    csv_size = sum(f.stat().st_size for f in (ARCHIVE_DIR / "csv").glob("*.csv")) / (1024*1024)
    audio_size = 0
    audio_dir = ARCHIVE_DIR / "audio"
    if audio_dir.exists():
        for root, dirs, files in os.walk(audio_dir):
            for f in files:
                audio_size += os.path.getsize(os.path.join(root, f))
        audio_size /= (1024 * 1024)

    print("-" * 40)
    print(f"Archive location: {ARCHIVE_DIR}")
    print(f"  DB backups:  {db_size:.1f} MB")
    print(f"  CSV exports: {csv_size:.1f} MB")
    if audio_size > 0:
        print(f"  Audio files: {audio_size:.1f} MB")
    print(f"  Total:       {db_size + csv_size + audio_size:.1f} MB")
    print()
    print("OneDrive will auto-sync these files to the cloud.")
    print("Done!")


if __name__ == "__main__":
    main()
