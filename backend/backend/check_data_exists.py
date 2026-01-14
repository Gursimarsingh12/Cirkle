#!/usr/bin/env python3
"""
Script to check if data already exists in the database.
Used by Docker entrypoint to prevent duplicate data generation.
"""
import asyncio
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

async def check_data_exists():
    """Check if users exist in the database."""
    try:
        from database.session import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as session:
            # Try to check if users table exists and has data
            try:
                result = await session.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()
                return user_count > 0
            except Exception as e:
                # Table might not exist or database not initialized
                print(f"Database check failed: {e}", file=sys.stderr)
                return False
                
    except Exception as e:
        print(f"Error connecting to database: {e}", file=sys.stderr)
        return False

def main():
    """Main function to check data existence and return exit code."""
    try:
        data_exists = asyncio.run(check_data_exists())
        if data_exists:
            print("Data exists")
            sys.exit(0)  # Success exit code - data exists
        else:
            print("No data found")
            sys.exit(1)  # Error exit code - no data
    except Exception as e:
        print(f"Script error: {e}", file=sys.stderr)
        sys.exit(1)  # Error exit code

if __name__ == "__main__":
    main() 