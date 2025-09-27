from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_session
from app.schemas.match import MatchRead, MatchListResponse, MatchCreate
from app.schemas.booking import BookingCreate, BookingRead, BookingListResponse
from app.schemas.player import JoinMatchRequest, LeaveMatchRequest
from app.schemas.venue import VenueListResponse
from app.schemas.kourt import KourtListResponse, KourtAvailabilityRequest
from app.services.match_service import MatchService
from app.services.booking_service import BookingService
from app.services.venue_service import VenueService
from app.services.kourt_service import KourtService


router = APIRouter(prefix="/public", tags=["public"])


@router.get("/kourts/{kourt_id}/availability")
async def get_kourt_availability(
    kourt_id: UUID,
    request: KourtAvailabilityRequest = Depends(),
    session: AsyncSession = Depends(get_session)
):
    """Get availability for a specific court on a given date."""
    return await KourtService.get_kourt_availability(kourt_id, request.date, session)


@router.post("/bookings", response_model=BookingRead)
async def create_booking(
    booking_data: BookingCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create a new booking for a court."""
    return await BookingService.create_public_booking(
        booking_data.kourt_id,
        booking_data.date,
        booking_data.start_time,
        booking_data.end_time,
        booking_data.customer_name,
        booking_data.customer_phone,
        session
    )


@router.get("/bookings/{booking_id}", response_model=BookingRead)
async def get_booking(
    booking_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """Get details of a specific booking by ID."""
    return await BookingService.get_public_booking(booking_id, session)


@router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(
    booking_id: UUID,
    cancellation_token: str,
    session: AsyncSession = Depends(get_session)
):
    """Cancel a booking using its cancellation token."""
    return await BookingService.cancel_public_booking(booking_id, cancellation_token, session)


@router.get("/venues", response_model=VenueListResponse)
async def list_venues(session: AsyncSession = Depends(get_session)):
    """List all public venues available for booking."""
    return await VenueService.list_public_venues(session)


@router.get("/venues/{venue_id}/kourts", response_model=KourtListResponse)
async def list_venue_kourts(
    venue_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """List all courts available in a specific venue."""
    return await KourtService.list_public_kourts(venue_id, session)


# --- MATCH ENDPOINTS ---

@router.post("/matches", response_model=MatchRead)
async def create_match(
    match_data: MatchCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create a new match for other players to join."""
    return await MatchService.create_match(
        creator_name=match_data.creator_name,
        creator_phone=match_data.creator_phone,
        date=match_data.date,
        start_time=match_data.start_time,
        end_time=match_data.end_time,
        max_players=match_data.max_players,
        session=session
    )

@router.get("/matches", response_model=MatchListResponse)
async def list_matches(session: AsyncSession = Depends(get_session)):
    """List all available matches that players can join."""
    return await MatchService.list_matches(session)


@router.post("/matches/{match_id}/join")
async def join_match(
    match_id: UUID,
    request: JoinMatchRequest,
    session: AsyncSession = Depends(get_session)
):
    """Join an existing match as a player."""
    return await MatchService.join_match(match_id, request.player_name, request.player_phone, session)


@router.get("/matches/{match_id}", response_model=MatchRead)
async def get_match_details(match_id: UUID, session: AsyncSession = Depends(get_session)):
    """Get detailed information about a specific match."""
    return await MatchService.get_match_details(match_id, session)


@router.post("/matches/{match_id}/leave")
async def leave_match(
    match_id: UUID,
    request: LeaveMatchRequest,
    session: AsyncSession = Depends(get_session)
):
    """Leave a match that you previously joined."""
    return await MatchService.leave_match(match_id, request.player_phone, session)