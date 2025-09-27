from fastapi import HTTPException, Depends, Header
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional
from app.core.database import get_session
from app.models.admin import Admin

async def get_admin_by_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-Api-Key"),
    session: AsyncSession = Depends(get_session)
) -> Admin:
    """
    FastAPI dependency to authenticate admin users via API key.
    
    Validates the X-Api-Key header against the database and returns
    the authenticated admin user for use in protected endpoints.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401, 
            detail="X-Api-Key header is required"
        )
    statement = select(Admin).where(Admin.api_key == x_api_key)
    result = await session.exec(statement)
    admin = result.first()
    if not admin:
        raise HTTPException(
            status_code=401, 
            detail="Invalid API key"
        )
    return admin

async def verify_admin_access(
    admin: Admin = Depends(get_admin_by_api_key)
) -> Admin:
    """
    FastAPI dependency for admin access verification.
    
    Currently passes through authenticated admin, but provides
    extension point for future authorization logic like role checks.
    """
    return admin
