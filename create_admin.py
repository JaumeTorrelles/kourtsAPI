"""
Script to create the first admin user for Kourts API.
Run this after setting up the database to get started.
"""

import asyncio
import secrets
from app.core.database import get_session
from app.models.admin import Admin

async def create_admin():
    """Create the first admin user with a secure API key."""
    
    # Get database session  
    async for session in get_session():
        try:
            # Generate secure API key
            admin_api_key = secrets.token_urlsafe(32)
            
            # Get admin details
            print("Creating first admin user...\n")
            
            name = input("Admin name: ").strip()
            if not name:
                name = "Admin User"
            
            email = input("Admin email: ").strip()
            if not email:
                print("Email is required!")
                return
                
            phone = input("Admin phone (optional): ").strip() or None
            
            # Create admin
            admin = Admin(
                name=name,
                email=email,
                phone=phone,
                api_key=admin_api_key
            )
            
            session.add(admin)
            await session.commit()
            await session.refresh(admin)
            
            print(f"\nAdmin created successfully!")
            print(f"API Key: {admin_api_key}")
            print(f"\nSave this API key - you'll need it for admin API calls!")
            print(f"   Add it to requests as: X-Api-Key: {admin_api_key}")
            break
            
        except Exception as e:
            await session.rollback()
            print(f"Error creating admin: {e}")
            break

if __name__ == "__main__":
    asyncio.run(create_admin())
