from fastapi import APIRouter, Depends, status, HTTPException
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import get_session
from ..services.auth_service import verify_admin_access
from ..models.admin import Admin
from ..schemas.venue import VenueCreate, VenueUpdate, VenueRead, VenueListResponse
from ..schemas.kourt import KourtCreate, KourtUpdate, KourtRead, KourtListResponse
from ..schemas.booking import BookingListResponse, BookingRead, BookingFilter
from ..services.venue_service import VenueService
from ..services.kourt_service import KourtService
from ..services.booking_service import BookingService


router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/venues", response_model=VenueRead, status_code=status.HTTP_201_CREATED)
async def create_venue(
    venue_data: VenueCreate,
    admin: Admin = Depends(verify_admin_access),
    session: AsyncSession = Depends(get_session)
):
    """Create a new venue for the authenticated admin."""
    return await VenueService.create_venue(venue_data, admin.id, session)

@router.get("/venues", response_model=VenueListResponse)
async def list_venues(
    admin: Admin = Depends(verify_admin_access),
    session: AsyncSession = Depends(get_session),
    skip: int = 0,
    limit: int = 100
):
    """List all venues owned by the authenticated admin."""
    return await VenueService.list_venues(admin.id, session, skip, limit)

@router.get("/venues/{venue_id}", response_model=VenueRead)
async def get_venue(
    venue_id: UUID,
    admin: Admin = Depends(verify_admin_access),
    session: AsyncSession = Depends(get_session)
):
    """Get details of a specific venue owned by the authenticated admin."""
    venue = await VenueService.get_venue(venue_id, admin.id, session)
    if not venue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")
    return venue

@router.patch("/venues/{venue_id}", response_model=VenueRead)
async def update_venue(
    venue_id: UUID,
    venue_data: VenueUpdate,
    admin: Admin = Depends(verify_admin_access),
    session: AsyncSession = Depends(get_session)
):
    """Update an existing venue owned by the authenticated admin."""
    venue = await VenueService.update_venue(venue_id, admin.id, venue_data, session)
    if not venue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")
    return venue

@router.delete("/venues/{venue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_venue(
    venue_id: UUID,
    admin: Admin = Depends(verify_admin_access),
    session: AsyncSession = Depends(get_session)
):
    """Delete a venue owned by the authenticated admin."""
    deleted = await VenueService.delete_venue(venue_id, admin.id, session)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")
    return None

@router.post("/venues/{venue_id}/kourts", response_model=KourtRead, status_code=status.HTTP_201_CREATED)
async def create_kourt(
    venue_id: UUID,
    kourt_data: KourtCreate,
    admin: Admin = Depends(verify_admin_access),
    session: AsyncSession = Depends(get_session)
):
    """Create a new court in the specified venue."""
    return await KourtService.create_kourt(venue_id, kourt_data, admin.id, session)

@router.get("/venues/{venue_id}/kourts", response_model=KourtListResponse)
async def list_kourts(
    venue_id: UUID,
    admin: Admin = Depends(verify_admin_access),
    session: AsyncSession = Depends(get_session),
    skip: int = 0,
    limit: int = 100
):
    """List all courts in the specified venue."""
    return await KourtService.list_kourts(venue_id, admin.id, session, skip, limit)

@router.get("/kourts/{kourt_id}", response_model=KourtRead)
async def get_kourt(
    kourt_id: UUID,
    admin: Admin = Depends(verify_admin_access),
    session: AsyncSession = Depends(get_session)
):
    """Get details of a specific court."""
    return await KourtService.get_kourt(kourt_id, admin.id, session)

@router.patch("/kourts/{kourt_id}", response_model=KourtRead)
async def update_kourt(
    kourt_id: UUID,
    kourt_data: KourtUpdate,
    admin: Admin = Depends(verify_admin_access),
    session: AsyncSession = Depends(get_session)
):
    """Update an existing court."""
    return await KourtService.update_kourt(kourt_id, admin.id, kourt_data, session)

@router.delete("/kourts/{kourt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kourt(
    kourt_id: UUID,
    admin: Admin = Depends(verify_admin_access),
    session: AsyncSession = Depends(get_session)
):
    """Delete a court owned by the authenticated admin."""
    deleted = await KourtService.delete_kourt(kourt_id, admin.id, session)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Court not found")
    return None

@router.get("/bookings", response_model=BookingListResponse)
async def list_bookings(
    filters: BookingFilter = Depends(),
    admin: Admin = Depends(verify_admin_access),
    session: AsyncSession = Depends(get_session)
):
    """List and filter bookings for venues owned by the authenticated admin."""
    return await BookingService.list_bookings(
        admin.id,
        session,
        filters.date_filter,
        filters.status,
        filters.customer_name,
        filters.skip,
        filters.limit
    )

@router.get("/bookings/{booking_id}", response_model=BookingRead)
async def get_booking_details(
    booking_id: UUID,
    admin: Admin = Depends(verify_admin_access),
    session: AsyncSession = Depends(get_session)
):
    """Get detailed information about a specific booking."""
    return await BookingService.get_booking_details(booking_id, admin.id, session)

@router.patch("/bookings/{booking_id}", response_model=BookingRead)
async def update_booking_status(
    booking_id: UUID,
    status: str,
    admin: Admin = Depends(verify_admin_access),
    session: AsyncSession = Depends(get_session)
):
    """Update the status of a specific booking."""
    return await BookingService.update_booking_status(booking_id, status, admin.id, session)
