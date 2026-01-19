#!/usr/bin/env python3
"""
Fix session lock issues by recreating the session file.
"""

import shutil
import sqlite3
from pathlib import Path

def fix_session_lock():
    """Fix locked session file by copying to a new file."""
    
    session_file = Path("telegram_scanner.session")
    backup_file = Path("telegram_scanner.session.backup")
    temp_file = Path("telegram_scanner_temp.session")
    
    print("Session Lock Fix Utility")
    print("=" * 50)
    
    if not session_file.exists():
        print("✗ No session file found")
        return False
    
    try:
        # Create backup
        print("Creating backup...")
        shutil.copy2(session_file, backup_file)
        print(f"✓ Backup created: {backup_file}")
        
        # Try to open and close the database to fix locks
        print("Attempting to fix database locks...")
        conn = sqlite3.connect(str(session_file))
        conn.execute("VACUUM")  # Rebuild database file
        conn.close()
        print("✓ Database vacuumed")
        
        # Copy to temp file
        print("Creating clean copy...")
        shutil.copy2(session_file, temp_file)
        
        # Replace original
        session_file.unlink()
        temp_file.rename(session_file)
        print("✓ Session file recreated")
        
        print("\n✓ Session lock fix completed successfully!")
        print(f"Backup saved as: {backup_file}")
        return True
        
    except Exception as e:
        print(f"✗ Error fixing session: {e}")
        
        # Try alternative method - just copy
        try:
            print("\nTrying alternative method...")
            if temp_file.exists():
                temp_file.unlink()
            
            # Read and write to new file
            with open(session_file, 'rb') as src:
                data = src.read()
            
            with open(temp_file, 'wb') as dst:
                dst.write(data)
            
            session_file.unlink()
            temp_file.rename(session_file)
            
            print("✓ Alternative method succeeded!")
            return True
            
        except Exception as e2:
            print(f"✗ Alternative method also failed: {e2}")
            
            # Restore from backup if it exists
            if backup_file.exists():
                print("Restoring from backup...")
                try:
                    if session_file.exists():
                        session_file.unlink()
                    shutil.copy2(backup_file, session_file)
                    print("✓ Restored from backup")
                except:
                    pass
            
            return False

if __name__ == "__main__":
    success = fix_session_lock()
    
    if success:
        print("\n" + "=" * 50)
        print("✓ You can now try running the scanner again")
        print("Run: python -m telegram_scanner.main")
    else:
        print("\n" + "=" * 50)
        print("✗ Could not fix session lock")
        print("Try:")
        print("1. Close all Python processes")
        print("2. Restart your computer")
        print("3. Delete telegram_scanner.session and re-authenticate")