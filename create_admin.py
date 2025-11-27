#!/usr/bin/env python3
"""
Script to create an admin user for Ticketmeister
Run this after setting up the database
"""

from flask_bcrypt import Bcrypt
from db_connection import get_db_connection as get_conn
from dotenv import load_dotenv

load_dotenv()

def create_admin_user():
    bcrypt = Bcrypt()
    
    print("=== Ticketmeister Admin User Creator ===\n")
    
    # Get user input
    first_name = input("First Name: ").strip()
    last_name = input("Last Name: ").strip()
    email = input("Email: ").strip()
    phone = input("Phone (optional): ").strip() or None
    username = input("Username: ").strip()
    password = input("Password: ")
    confirm_password = input("Confirm Password: ")
    
    # Validation
    if not all([first_name, last_name, email, username, password]):
        print("\n❌ Error: All required fields must be filled!")
        return
    
    if password != confirm_password:
        print("\n❌ Error: Passwords do not match!")
        return
    
    if len(password) < 6:
        print("\n❌ Error: Password must be at least 6 characters!")
        return
    
    try:
        with get_conn() as conn, conn.cursor() as cur:
            # Check if username exists
            cur.execute("SELECT user_id FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                print(f"\n❌ Error: Username '{username}' already exists!")
                return
            
            # Check if email exists
            cur.execute("SELECT person_id FROM persons WHERE email = %s", (email,))
            if cur.fetchone():
                print(f"\n❌ Error: Email '{email}' already registered!")
                return
            
            # Create person record
            cur.execute("""
                INSERT INTO persons (first_name, last_name, email, phone)
                VALUES (%s, %s, %s, %s)
            """, (first_name, last_name, email, phone))
            person_id = cur.lastrowid
            print(f"✓ Created person record (ID: {person_id})")
            
            # Create customer record
            cur.execute("""
                INSERT INTO customers (person_id, loyalty_points)
                VALUES (%s, 0)
            """, (person_id,))
            print(f"✓ Created customer record")
            
            # Create admin user record
            password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            cur.execute("""
                INSERT INTO users (person_id, username, password_hash, is_admin, is_active)
                VALUES (%s, %s, %s, 1, 1)
            """, (person_id, username, password_hash))
            user_id = cur.lastrowid
            print(f"✓ Created admin user (ID: {user_id})")
            
            conn.commit()
            
            print(f"\n✅ Admin user created successfully!")
            print(f"\nLogin credentials:")
            print(f"  Username: {username}")
            print(f"  Password: [hidden]")
            print(f"\nYou can now log in at: http://localhost:5000/login")
            
    except Exception as e:
        print(f"\n❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_admin_user()