import shutil
from pathlib import Path
from datetime import datetime

BACKUP_DIR = Path(__file__).parent / "backups"
DB_PATH = Path(__file__).parent / "data" / "settlement.db"

def list_backups():
    """사용 가능한 백업 목록 표시"""
    if not BACKUP_DIR.exists():
        print("No backups found")
        return []

    backups = sorted(BACKUP_DIR.glob("settlement_*.db"), reverse=True)
    for i, backup in enumerate(backups, 1):
        size = backup.stat().st_size / (1024 * 1024)  # MB
        print(f"{i}. {backup.name} ({size:.2f}MB)")

    return backups

def restore_backup(index: int):
    """특정 백업에서 복구"""
    backups = list_backups()

    if not backups or index < 1 or index > len(backups):
        print("Invalid backup index")
        return False

    backup_file = backups[index - 1]

    # 현재 DB를 안전하게 저장
    if DB_PATH.exists():
        broken_backup = BACKUP_DIR / f"broken_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(DB_PATH, broken_backup)
        print(f"Current DB saved as: {broken_backup.name}")

    # 복구
    shutil.copy2(backup_file, DB_PATH)
    print(f"✓ Restored from: {backup_file.name}")

    return True

if __name__ == "__main__":
    print("=== Available Backups ===")
    list_backups()

    choice = input("\nEnter backup number to restore (0 to cancel): ")
    if choice != "0":
        try:
            restore_backup(int(choice))
        except ValueError:
            print("Invalid input")
