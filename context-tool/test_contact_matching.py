#!/usr/bin/env python3
"""Test contact matching to debug why names aren't being found"""

import sqlite3
from pathlib import Path
from src.database import get_database
from src.data_loaders import load_data

# Initialize database
db_obj = get_database(":memory:")
db = db_obj.connection

# Load markdown data
data_dir = Path("./data-md")
load_data(db, data_dir, format='markdown')

print("=" * 60)
print("Testing Contact Matching")
print("=" * 60)

# List all contacts
print("\n📋 All contacts in database:")
cursor = db.execute("SELECT id, name, email FROM contacts")
contacts = cursor.fetchall()
for contact in contacts:
    print(f"   - {contact[1]} ({contact[2]})")

# Test search queries
test_names = [
    "Emma Rodriguez",
    "Emma",
    "Rodriguez",
    "Sarah Mitchell",
    "Sarah",
    "stefan krona"
]

print("\n🔍 Testing search queries:")
for test_name in test_names:
    cursor = db.execute("""
        SELECT name, email FROM contacts
        WHERE name LIKE ? OR email LIKE ?
    """, (f'%{test_name}%', f'%{test_name}%'))

    results = cursor.fetchall()
    print(f"\n   Query: '{test_name}'")
    if results:
        for result in results:
            print(f"      ✓ Found: {result[0]} ({result[1]})")
    else:
        print(f"      ✗ No matches")

print("\n" + "=" * 60)
