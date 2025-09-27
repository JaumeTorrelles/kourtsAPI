import json
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
from app.models.venue import Venue
from app.schemas.venue import VenueCreate, VenueUpdate, VenueRead, VenueListResponse
from fastapi import HTTPException

class VenueService:
    @staticmethod
    async def list_public_venues(session: AsyncSession, skip: int = 0, limit: int = 100) -> VenueListResponse:
        """
        Lists all public venues with pagination support.
        This endpoint is used by customers to browse available venues.
        
        Args:
            session: Database session
            skip: Number of records to skip for pagination (default: 0)
            limit: Maximum number of records to return (default: 100)
            
        Returns:
            VenueListResponse: Paginated list of venues with total count
        """
        count_statement = select(func.count(Venue.id))
        total = await session.exec(count_statement)
        total_count = total.first()
        statement = select(Venue).offset(skip).limit(limit)
        result = await session.exec(statement)
        venues = result.all()
        venue_reads = [VenueRead.model_validate(v) for v in venues]
        return VenueListResponse(venues=venue_reads, total=total_count)
    @staticmethod
    async def create_venue(venue_data: VenueCreate, admin_id: UUID, session: AsyncSession) -> VenueRead:
        """
        Creates a new venue with JSON-serialized opening hours.
        Only the authenticated admin can create venues they will own.
        
        Args:
            venue_data: Venue creation data including name, location, opening hours
            admin_id: UUID of the admin creating the venue
            session: Database session
            
        Returns:
            VenueRead: The newly created venue
            
        Note:
            Opening hours are stored as JSON in the database for flexible scheduling
        """
        venue_dict = venue_data.model_dump()
        if 'opening_hours' in venue_dict and isinstance(venue_dict['opening_hours'], dict):
            venue_dict['opening_hours'] = json.dumps(venue_dict['opening_hours'])
        venue = Venue(**venue_dict, admin_id=admin_id)
        session.add(venue)
        await session.commit()
        await session.refresh(venue)
        return VenueRead.model_validate(venue)

    @staticmethod
    async def list_venues(admin_id: UUID, session: AsyncSession, skip: int = 0, limit: int = 100) -> VenueListResponse:
        """
        Lists all venues owned by a specific admin with pagination.
        This is the admin dashboard view showing only venues they manage.
        
        Args:
            admin_id: UUID of the admin requesting their venues
            session: Database session
            skip: Number of records to skip for pagination (default: 0)
            limit: Maximum number of records to return (default: 100)
            
        Returns:
            VenueListResponse: Paginated list of admin's venues with total count
        """
        count_statement = select(func.count(Venue.id)).where(Venue.admin_id == admin_id)
        total = await session.exec(count_statement)
        total_count = total.first()
        statement = select(Venue).where(Venue.admin_id == admin_id).offset(skip).limit(limit)
        result = await session.exec(statement)
        venues = result.all()
        venue_reads = [VenueRead.model_validate(v) for v in venues]
        return VenueListResponse(venues=venue_reads, total=total_count)

    @staticmethod
    async def get_venue(venue_id: UUID, admin_id: UUID, session: AsyncSession) -> VenueRead:
        """
        Retrieves a specific venue by ID. Only the venue owner can access it.
        
        Args:
            venue_id: UUID of the venue to retrieve
            admin_id: UUID of the admin requesting the venue
            session: Database session
            
        Returns:
            VenueRead: The requested venue details
            
        Raises:
            HTTPException: If venue not found or admin doesn't own it (404)
        """
        statement = select(Venue).where(Venue.id == venue_id, Venue.admin_id == admin_id)
        result = await session.exec(statement)
        venue = result.first()
        if not venue:
            raise HTTPException(status_code=404, detail="Venue not found")
        return VenueRead.model_validate(venue)

    @staticmethod
    async def update_venue(venue_id: UUID, admin_id: UUID, venue_data: VenueUpdate, session: AsyncSession) -> VenueRead:
        """
        Updates an existing venue with proper JSON serialization for opening hours.
        Only the venue owner can update their venues.
        
        Args:
            venue_id: UUID of the venue to update
            admin_id: UUID of the admin updating the venue
            venue_data: Updated venue data (only non-null fields will be applied)
            session: Database session
            
        Returns:
            VenueRead: The updated venue details
            
        Raises:
            HTTPException: If venue not found or admin doesn't own it (404)
        """
        statement = select(Venue).where(Venue.id == venue_id, Venue.admin_id == admin_id)
        result = await session.exec(statement)
        venue = result.first()
        if not venue:
            raise HTTPException(status_code=404, detail="Venue not found")
        update_data = venue_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == 'opening_hours' and isinstance(value, dict):
                setattr(venue, field, json.dumps(value))
            else:
                setattr(venue, field, value)
        session.add(venue)
        await session.commit()
        await session.refresh(venue)
        return VenueRead.model_validate(venue)

    @staticmethod
    async def delete_venue(venue_id: UUID, admin_id: UUID, session: AsyncSession) -> bool:
        """
        Deletes a venue if it has no associated courts or bookings.
        This prevents data integrity issues by checking relationships first.
        Only the venue owner can delete their venues.
        
        Args:
            venue_id: UUID of the venue to delete
            admin_id: UUID of the admin deleting the venue
            session: Database session
            
        Returns:
            bool: True if deletion was successful
            
        Raises:
            HTTPException: If venue not found (404) or has associated courts/bookings (400)
        """
        statement = select(Venue).where(Venue.id == venue_id, Venue.admin_id == admin_id)
        result = await session.exec(statement)
        venue = result.first()
        if not venue:
            raise HTTPException(status_code=404, detail="Venue not found")
        
        # Check if there are related courts (import here to avoid circular dependency)
        from app.models.kourt import Kourt
        kourt_stmt = select(Kourt).where(Kourt.venue_id == venue_id)
        kourt_result = await session.exec(kourt_stmt)
        kourts = kourt_result.all()
        
        if kourts:
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete venue that has associated courts. Please delete the courts first."
            )
        
        # Check if there are related bookings (import here to avoid circular dependency)
        from app.models.booking import Booking
        booking_stmt = select(Booking).where(Booking.venue_id == venue_id)
        booking_result = await session.exec(booking_stmt)
        bookings = booking_result.all()
        
        if bookings:
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete venue that has associated bookings. Please delete the bookings first."
            )
        
        await session.delete(venue)
        await session.commit()
        return True
