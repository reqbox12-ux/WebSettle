import shutil
import sqlite3
from pathlib import Path
from datetime import datetime

BACKUP_DIR = Path(__file__).parent / "backups"
DB_PATH = Path(__file__).parent / "data" / "settlement.db"

def create_backup():
    """일일 자동 백업 생성"""
    BACKUP_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 데이터베이스 백업
    if DB_PATH.exists():
        backup_db = BACKUP_DIR / f"settlement_{timestamp}.db"
        shutil.copy2(DB_PATH, backup_db)
        print(f"[OK] Database backup: {backup_db.name}")

    # 매핑 파일 백업
    mapping_dir = Path(__file__).parent / "mapping"
    if mapping_dir.exists():
        backup_mapping = BACKUP_DIR / f"mapping_{timestamp}"
        if backup_mapping.exists():
            shutil.rmtree(backup_mapping)
        shutil.copytree(mapping_dir, backup_mapping)
        print(f"[OK] Mapping backup: {backup_mapping.name}")

    # 최근 7개 백업만 유지
    backups = sorted(BACKUP_DIR.glob("settlement_*.db"))
    for old_backup in backups[:-7]:
        old_backup.unlink()

    print(f"[OK] Backup completed at {timestamp}")

if __name__ == "__main__":
    create_backup()
