"""
Database migration script for Task Buddy
Adds new columns for admin dashboard and review system
"""

import sqlite3
from datetime import datetime

def migrate_database():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    
    print("Starting database migration...")
    
    try:
        # Add columns to User table
        print("Adding is_admin column to User table...")
        cursor.execute("ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0")
        print("✓ is_admin column added")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✓ is_admin column already exists")
        else:
            print(f"Error adding is_admin: {e}")
    
    try:
        print("Adding created_at column to User table...")
        cursor.execute("ALTER TABLE user ADD COLUMN created_at VARCHAR(50)")
        print("✓ created_at column added")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✓ created_at column already exists")
        else:
            print(f"Error adding created_at: {e}")
    
    # Add columns to Task table
    try:
        print("Adding is_deleted column to Task table...")
        cursor.execute("ALTER TABLE task ADD COLUMN is_deleted BOOLEAN DEFAULT 0")
        print("✓ is_deleted column added")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✓ is_deleted column already exists")
        else:
            print(f"Error adding is_deleted: {e}")
    
    try:
        print("Adding deleted_at column to Task table...")
        cursor.execute("ALTER TABLE task ADD COLUMN deleted_at VARCHAR(50)")
        print("✓ deleted_at column added")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✓ deleted_at column already exists")
        else:
            print(f"Error adding deleted_at: {e}")
    
    # Create Review table
    try:
        print("Creating Review table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS review (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                text VARCHAR(500),
                created_at VARCHAR(50),
                is_approved BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        """)
        print("✓ Review table created")
    except sqlite3.OperationalError as e:
        print(f"Error creating review table: {e}")
    
    # Create an admin user (optional)
    print("\nChecking for admin user...")
    cursor.execute("SELECT COUNT(*) FROM user WHERE is_admin = 1")
    admin_count = cursor.fetchone()[0]
    
    if admin_count == 0:
        print("No admin user found. You can make a user admin later.")
        print("To make a user admin, use: UPDATE user SET is_admin = 1 WHERE email = 'your@email.com'")
    else:
        print(f"✓ Found {admin_count} admin user(s)")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Database migration completed successfully!")
    print("\nNext steps:")
    print("1. To create an admin user, register normally then run:")
    print("   python -c \"import sqlite3; c=sqlite3.connect('tasks.db'); c.execute('UPDATE user SET is_admin=1 WHERE email=\\\"YOUR_EMAIL\\\"'); c.commit()\"")
    print("2. Restart your server: python server.py")

if __name__ == '__main__':
    migrate_database()
