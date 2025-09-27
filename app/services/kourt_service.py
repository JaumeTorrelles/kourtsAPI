from uuid import UUID
from sqlmodel import select, func
from fastapi import HTTPException, status
from datetime import date, time, datetime
from typing import List, Dict, Optional

from app.models.kourt import Kourt
from app.models.venue import Venue
from app.models.booking import Booking
from app.schemas.kourt import KourtCreate, KourtUpdate, KourtRead, KourtListResponse, KourtAvailabilityResponse

class KourtService:
    @staticmethod
    async def get_kourt_availability(kourt_id: UUID, date: date, session) -> KourtAvailabilityResponse:
        """
        Returns court availability for a specific date with available time slots.
        """
        try:
            from app.services.booking_service import calculate_available_intervals
            current_date = datetime.now().date()
            if date < current_date:
                raise HTTPException(status_code=400, detail="Cannot check availability for past dates")
            
            result = await session.exec(select(Kourt).where(Kourt.id == kourt_id))
            kourt = result.first()
            if not kourt:
                raise HTTPException(status_code=404, detail="Court not found")
            if not kourt.active:
                raise HTTPException(status_code=400, detail="This court is not available")
            
            result = await session.exec(select(Venue).where(Venue.id == kourt.venue_id))
            venue = result.first()
            if not venue:
                raise HTTPException(status_code=404, detail="Venue not found")
            
            result = await session.exec(
                select(Booking)
                .where(Booking.venue_id == venue.id)
                .where(Booking.date == date)
                .where(Booking.status == "Booked")
            )
            bookings = result.all()
            
            
            available_intervals = calculate_available_intervals(
                venue=venue,
                kourt=kourt,
                target_date=date,
                existing_bookings=bookings,
                interval_minutes=30
            )
            return KourtAvailabilityResponse.model_validate({
                "available_intervals": available_intervals,
                "total_available": len(available_intervals),
                "message": f"There are {len(available_intervals)} available time slots"
            })
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    @staticmethod
    async def list_public_kourts(venue_id: UUID, session, skip: int = 0, limit: int = 100) -> KourtListResponse:
        """
        Returns all active courts for a venue in KourtListResponse format.
        """
        venue_statement = select(Venue).where(Venue.id == venue_id)
        venue_result = await session.exec(venue_statement)
        venue = venue_result.first()
        if not venue:
            raise HTTPException(status_code=404, detail="Venue not found")
        count_statement = select(func.count(Kourt.id)).where(Kourt.venue_id == venue_id, Kourt.active == True)
        total = await session.exec(count_statement)
        total_count = total.first()
        statement = select(Kourt).where(Kourt.venue_id == venue_id, Kourt.active == True).offset(skip).limit(limit)
        result = await session.exec(statement)
        kourts = result.all()
        kourt_responses = [
            KourtRead(
                id=k.id,
                venue_id=k.venue_id,
                name=k.name,
                type=k.type,
                capacity=k.capacity,
                active=k.active,
                created_at=k.created_at
            ) for k in kourts
        ]
        return KourtListResponse(kourts=kourt_responses, total=total_count)
    @staticmethod
    async def create_kourt(venue_id: UUID, kourt_data: KourtCreate, admin_id: UUID, session) -> KourtRead:
        """
        Creates a new court for a venue. Only the venue owner (admin) can create courts.
        
        Args:
            venue_id: ID of the venue where the court will be created
            kourt_data: Court data from the request
            admin_id: ID of the admin creating the court
            session: Database session
            
        Returns:
            KourtRead: The newly created court
            
        Raises:
            HTTPException: If venue not found or admin doesn't own the venue
        """
        venue_statement = select(Venue).where(Venue.id == venue_id, Venue.admin_id == admin_id)
        venue_result = await session.exec(venue_statement)
        venue = venue_result.first()
        if not venue:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")
        kourt = Kourt(**kourt_data.model_dump(), venue_id=venue_id)
        session.add(kourt)
        await session.commit()
        await session.refresh(kourt)
        return KourtRead.model_validate(kourt)

    @staticmethod
    async def list_kourts(venue_id: UUID, admin_id: UUID, session, skip: int = 0, limit: int = 100) -> KourtListResponse:
        """
        Lists all courts for a venue (admin view - includes inactive courts).
        Only the venue owner (admin) can access this list.
        
        Args:
            venue_id: ID of the venue
            admin_id: ID of the admin requesting the list
            session: Database session
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            
        Returns:
            KourtListResponse: Paginated list of courts with total count
            
        Raises:
            HTTPException: If venue not found or admin doesn't own the venue
        """
        venue_statement = select(Venue).where(Venue.id == venue_id, Venue.admin_id == admin_id)
        venue_result = await session.exec(venue_statement)
        venue = venue_result.first()
        if not venue:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")
        count_statement = select(func.count(Kourt.id)).where(Kourt.venue_id == venue_id)
        total = await session.exec(count_statement)
        total_count = total.first()
        statement = select(Kourt).where(Kourt.venue_id == venue_id).offset(skip).limit(limit)
        result = await session.exec(statement)
        kourts = result.all()
        kourt_responses = [KourtRead.model_validate(k) for k in kourts]
        return KourtListResponse(kourts=kourt_responses, total=total_count)

    @staticmethod
    async def get_kourt(kourt_id: UUID, admin_id: UUID, session) -> KourtRead:
        """
        Gets a specific court by ID. Only the venue owner (admin) can access court details.
        
        Args:
            kourt_id: ID of the court to retrieve
            admin_id: ID of the admin requesting the court
            session: Database session
            
        Returns:
            KourtRead: The requested court details
            
        Raises:
            HTTPException: If court not found or admin doesn't own the venue
        """
        statement = select(Kourt).join(Venue).where(Kourt.id == kourt_id, Venue.admin_id == admin_id)
        result = await session.exec(statement)
        kourt = result.first()
        if not kourt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Court not found")
        return KourtRead.model_validate(kourt)

    @staticmethod
    async def update_kourt(kourt_id: UUID, admin_id: UUID, kourt_data: KourtUpdate, session) -> KourtRead:
        """
        Updates an existing court. Only the venue owner (admin) can update courts.
        
        Args:
            kourt_id: ID of the court to update
            admin_id: ID of the admin updating the court
            kourt_data: Updated court data (only non-null fields will be updated)
            session: Database session
            
        Returns:
            KourtRead: The updated court details
            
        Raises:
            HTTPException: If court not found or admin doesn't own the venue
        """
        statement = select(Kourt).join(Venue).where(Kourt.id == kourt_id, Venue.admin_id == admin_id)
        result = await session.exec(statement)
        kourt = result.first()
        if not kourt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Court not found")
        for key, value in kourt_data.model_dump(exclude_unset=True).items():
            setattr(kourt, key, value)
        session.add(kourt)
        await session.commit()
        await session.refresh(kourt)
        return KourtRead.model_validate(kourt)

    @staticmethod
    async def delete_kourt(kourt_id: UUID, admin_id: UUID, session):
        """
        Soft deletes a court by setting it as inactive. Only the venue owner (admin) can delete courts.
        This is a soft delete to preserve booking history and referential integrity.
        
        Args:
            kourt_id: ID of the court to delete
            admin_id: ID of the admin deleting the court
            session: Database session
            
        Returns:
            dict: Success message
            
        Raises:
            HTTPException: If court not found or admin doesn't own the venue
        """
        statement = select(Kourt).join(Venue).where(Kourt.id == kourt_id, Venue.admin_id == admin_id)
        result = await session.exec(statement)
        kourt = result.first()
        if not kourt:
            return False
        
        # Check if there are related bookings
        from app.models.booking import Booking
        booking_stmt = select(Booking).where(Booking.kourt_id == kourt_id)
        booking_result = await session.exec(booking_stmt)
        bookings = booking_result.all()
        
        if bookings:
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete a court that has associated bookings. Please delete the bookings first."
            )
        
        await session.delete(kourt)
        await session.commit()
        return True

    @staticmethod
    def generate_time_intervals(start_time: time, end_time: time, interval_minutes: int = 30) -> List[time]:
        """
        Generates a list of time intervals between start_time and end_time.
        
        Args:
            start_time: Starting time for intervals
            end_time: Ending time for intervals
            interval_minutes: Minutes between each interval (default: 30)
            
        Returns:
            List[time]: List of time objects representing available slots
        """
        intervals = []
        start_minutes = start_time.hour * 60 + start_time.minute
        end_minutes = end_time.hour * 60 + end_time.minute
        current_minutes = start_minutes
        while current_minutes + interval_minutes <= end_minutes:
            hours = current_minutes // 60
            minutes = current_minutes % 60
            interval_time = time(hour=hours, minute=minutes)
            intervals.append(interval_time)
            current_minutes += interval_minutes
        return intervals

    @staticmethod
    def get_venue_opening_hours_for_date(venue, target_date: date) -> Optional[Dict[str, str]]:
        """
        Gets the opening hours for a venue on a specific date.
        
        Args:
            venue: Venue object with opening_hours_dict property
            target_date: Date to get opening hours for
            
        Returns:
            Optional[Dict[str, str]]: Opening hours dict for the day or None if closed
        """
        opening_hours = venue.opening_hours_dict
        weekday_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        weekday = weekday_names[target_date.weekday()]
        return opening_hours.get(weekday)
