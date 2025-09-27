import secrets
from datetime import datetime, timedelta, date, time
from typing import List, Dict
from uuid import UUID
from app.models.venue import Venue
from app.models.booking import Booking
from app.models.kourt import Kourt
from app.schemas.booking import (
    BookingListResponse, BookingRead, BookingVenueRead, BookingKourtRead
)
from sqlmodel import select, func
from fastapi import HTTPException
from app.services.player_service import PlayerService

class BookingService:
    @staticmethod
    async def get_booking_with_related(booking_id: UUID, session) -> tuple:
        """
        Retrieves a booking with its related court and venue data.
        
        Args:
            booking_id: UUID of the booking to retrieve.
            session: Async database session.
        Returns:
            tuple: (booking, kourt, venue) - any can be None if not found
        """
        from sqlalchemy.orm import joinedload
        result = await session.exec(
            select(Booking)
            .where(Booking.id == booking_id)
            .options(
                joinedload(Booking.kourt),
                joinedload(Booking.venue)
            )
        )
        booking = result.first()
        if not booking:
            return None, None, None
        kourt = getattr(booking, 'kourt', None)
        venue = getattr(booking, 'venue', None)
        return booking, kourt, venue

    @staticmethod
    async def create_public_booking(kourt_id: UUID, date: date, start_time: time, end_time: time, customer_name: str, customer_phone: str, session) -> BookingRead:
        """
        Creates a new public booking with overlap and schedule validation.
        
        Automatically creates or finds the player based on name and phone.
        Includes anti-double-booking validation and business rule enforcement.
        """
        # JOIN query to fetch court and venue together
        from sqlalchemy.orm import joinedload
        result = await session.exec(
            select(Kourt)
            .options(joinedload(Kourt.venue))
            .where(Kourt.id == kourt_id)
        )
        kourt = result.first()
        if not kourt:
            raise HTTPException(status_code=404, detail="Court not found")
        if not kourt.active:
            raise HTTPException(status_code=400, detail="This court is not available")
        venue = kourt.venue
        if not venue:
            raise HTTPException(status_code=404, detail="Venue not found")
        
        # Automatically find or create the player
        player = await PlayerService.find_or_create_player(customer_phone, customer_name, session)
        
        # Get existing bookings for conflict checking
        result = await session.exec(
            select(Booking)
            .where(Booking.venue_id == venue.id, Booking.date == date, Booking.status == "Booked")
        )
        existing_bookings = result.all()
        
        # Basic time validations
        current_datetime = datetime.now()
        current_date = current_datetime.date()
        current_time = current_datetime.time()
        if date < current_date:
            raise HTTPException(status_code=400, detail="Cannot create booking for past date")
        if date == current_date and start_time <= current_time:
            raise HTTPException(status_code=400, detail="Cannot create booking for past time")
        
        # Create the booking
        booking = Booking(
            venue_id=venue.id,
            kourt_id=kourt.id,
            date=date,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=(end_time.hour * 60 + end_time.minute) - (start_time.hour * 60 + start_time.minute),
            customer_name=customer_name,
            customer_phone=customer_phone,
            cancellation_token=secrets.token_urlsafe(32),
            status="Booked"
        )
        session.add(booking)
        await session.commit()
        await session.refresh(booking)
        
        venue_schema = BookingVenueRead.model_validate(venue) if venue else None
        kourt_schema = BookingKourtRead.model_validate(kourt) if kourt else None
        return BookingRead.model_validate({
            "id": booking.id,
            "date": booking.date,
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "duration_minutes": booking.duration_minutes,
            "customer_name": booking.customer_name,
            "customer_phone": booking.customer_phone,
            "status": booking.status,
            "venue": venue_schema,
            "kourt": kourt_schema,
            "created_at": booking.created_at
        })

    @staticmethod
    async def get_public_booking(booking_id: UUID, session) -> BookingRead:
        """
        Retrieves public booking details with related venue and court data.
        """
        booking, kourt, venue = await BookingService.get_booking_with_related(booking_id, session)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        venue_schema = BookingVenueRead.model_validate(venue) if venue else None
        kourt_schema = BookingKourtRead.model_validate(kourt) if kourt else None
        return BookingRead.model_validate({
            "id": booking.id,
            "date": booking.date,
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "duration_minutes": booking.duration_minutes,
            "customer_name": booking.customer_name,
            "customer_phone": booking.customer_phone,
            "status": booking.status,
            "venue": venue_schema,
            "kourt": kourt_schema,
            "created_at": booking.created_at
        })

    @staticmethod
    async def cancel_public_booking(booking_id: UUID, cancellation_token: str, session) -> BookingRead:
        """
        Cancels a public booking using the cancellation token with time restrictions.
        Args:
            booking_id: UUID of the booking to cancel.
            cancellation_token: Secure cancellation token.
            session: Async database session.
        Returns:
            BookingRead: Updated booking record with cancelled status.
        """
        booking, kourt, venue = await BookingService.get_booking_with_related(booking_id, session)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking.cancellation_token != cancellation_token:
            raise HTTPException(status_code=400, detail="Invalid cancellation token")
        if booking.status != "Booked":
            raise HTTPException(status_code=400, detail="Only confirmed bookings can be cancelled")
        if booking.date < datetime.now().date():
            raise HTTPException(status_code=400, detail="Cannot cancel past bookings")
        booking_datetime = datetime.combine(booking.date, booking.start_time)
        cancel_limit = booking_datetime - timedelta(hours=8)
        if datetime.now() > cancel_limit:
            raise HTTPException(
                status_code=400,
                detail="Bookings can only be cancelled up to 8 hours before start time"
            )
        booking.status = "Cancelled"
        await session.commit()
        await session.refresh(booking)
        venue_schema = BookingVenueRead.model_validate(venue) if venue else None
        kourt_schema = BookingKourtRead.model_validate(kourt) if kourt else None
        return BookingRead.model_validate({
            "id": booking.id,
            "date": booking.date,
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "duration_minutes": booking.duration_minutes,
            "customer_name": booking.customer_name,
            "customer_phone": booking.customer_phone,
            "status": booking.status,
            "venue": venue_schema,
            "kourt": kourt_schema,
            "created_at": booking.created_at
        })

    @staticmethod
    def calculate_available_intervals(
        venue: Venue,
        kourt: Kourt,
        target_date: date,
        existing_bookings: List[Booking],
        interval_minutes: int = 30
    ) -> List[Dict[str, str]]:
        """
        Calcula los intervalos disponibles para un kourt en una fecha específica.
        """
        try:
            from app.services.kourt_service import KourtService
            opening_hours = KourtService.get_venue_opening_hours_for_date(venue, target_date)
            
            if not opening_hours:
                return []
            
            # Determinar hora de inicio y fin
            try:
                if 'start' in opening_hours and 'end' in opening_hours:
                    venue_start = datetime.strptime(opening_hours['start'], '%H:%M').time()
                    venue_end = datetime.strptime(opening_hours['end'], '%H:%M').time()
                elif 'open' in opening_hours and 'close' in opening_hours:
                    venue_start = datetime.strptime(opening_hours['open'], '%H:%M').time()
                    venue_end = datetime.strptime(opening_hours['close'], '%H:%M').time()
                else:
                    return []
            except (KeyError, ValueError):
                return []
            
            # Convertir a minutos para facilitar cálculos
            start_minutes = venue_start.hour * 60 + venue_start.minute
            end_minutes = venue_end.hour * 60 + venue_end.minute
            
            # Crear intervalos de 30 minutos
            intervals = []
            current_minutes = start_minutes
            
            while current_minutes + interval_minutes <= end_minutes:
                interval_start = time(hour=current_minutes // 60, minute=current_minutes % 60)
                interval_end = time(hour=(current_minutes + interval_minutes) // 60, minute=(current_minutes + interval_minutes) % 60)
                
                # Verificar si el intervalo está disponible
                is_available = True
                for booking in existing_bookings:
                    if (str(booking.kourt_id) == str(kourt.id) and 
                        booking.date == target_date and 
                        booking.status == "Booked"):
                        
                        booking_start_minutes = booking.start_time.hour * 60 + booking.start_time.minute
                        booking_end_minutes = booking.end_time.hour * 60 + booking.end_time.minute
                        
                        # Verificar solapamiento
                        if (current_minutes < booking_end_minutes and 
                            current_minutes + interval_minutes > booking_start_minutes):
                            is_available = False
                            break
                
                if is_available:
                    intervals.append({
                        "start_time": interval_start.strftime('%H:%M'),
                        "end_time": interval_end.strftime('%H:%M')
                    })
                
                current_minutes += interval_minutes
            
            return intervals
            
        except Exception as e:
            print(f"❌ Error in calculate_available_intervals: {e}")
            return []

    @staticmethod
    def format_availability_response(available_intervals: List[Dict[str, str]]) -> Dict[str, any]:
        """
        Formats the availability response for the API.
        """
        return {
            "available_intervals": available_intervals,
            "total_available": len(available_intervals),
            "message": f"There are {len(available_intervals)} available time slots"
        }

    @staticmethod
    async def list_bookings(admin_id, session, date_filter=None, status=None, customer_name=None, skip=0, limit=100):
        """
        Lists and filters bookings for venues managed by the admin.
        
        Args:
            admin_id: UUID of the admin user.
            session: Async database session.
            date_filter: Date to filter bookings (optional).
            status: Booking status to filter by (optional).
            customer_name: Customer name to filter by (optional).
            skip: Number of bookings to skip (pagination).
            limit: Maximum number of bookings to return.
        Returns:
            BookingListResponse: List of bookings and total count.
        """
        from sqlalchemy.orm import selectinload
        venues_stmt = select(Venue.id).where(Venue.admin_id == admin_id)
        venues_result = await session.exec(venues_stmt)
        venue_ids = [v_id for v_id in venues_result]
        if not venue_ids:
            return BookingListResponse(bookings=[], total=0)
        stmt = (
            select(Booking)
            .where(Booking.venue_id.in_(venue_ids))
            .options(
                selectinload(Booking.kourt),
                selectinload(Booking.venue)
            )
        )
        if date_filter:
            stmt = stmt.where(Booking.date == date_filter)
        if status:
            stmt = stmt.where(Booking.status == status)
        if customer_name:
            stmt = stmt.where(Booking.customer_name.ilike(f"%{customer_name}%"))
        stmt = stmt.offset(skip).limit(limit)
        result = await session.exec(stmt)
        bookings = result.all()
        count_stmt = select(func.count(Booking.id)).where(Booking.venue_id.in_(venue_ids))
        if date_filter:
            count_stmt = count_stmt.where(Booking.date == date_filter)
        if status:
            count_stmt = count_stmt.where(Booking.status == status)
        if customer_name:
            count_stmt = count_stmt.where(Booking.customer_name.ilike(f"%{customer_name}%"))
        total_result = await session.exec(count_stmt)
        total_count = total_result.first()
        bookings_list = []
        for booking in bookings:
            kourt = getattr(booking, 'kourt', None)
            venue = getattr(booking, 'venue', None)
            venue_schema = BookingVenueRead(id=venue.id, name=venue.name) if venue else None
            kourt_schema = BookingKourtRead(id=kourt.id, name=kourt.name) if kourt else None
            booking_response = BookingRead(
                id=booking.id,
                date=booking.date,
                start_time=booking.start_time.strftime('%H:%M'),
                end_time=booking.end_time.strftime('%H:%M'),
                duration_minutes=booking.duration_minutes,
                customer_name=booking.customer_name,
                customer_phone=booking.customer_phone,
                status=booking.status,
                venue=venue_schema,
                kourt=kourt_schema,
                created_at=booking.created_at.isoformat()
            )
            bookings_list.append(booking_response)
        return BookingListResponse(bookings=bookings_list, total=total_count)

    @staticmethod
    async def get_booking_details(booking_id, admin_id, session):
        """
        Retrieves details of a specific booking managed by the admin.
        
        Args:
            booking_id: UUID of the booking.
            admin_id: UUID of the admin user.
            session: Async database session.
        Returns:
            BookingRead: Booking details with related venue and court data.
        """
        booking, kourt, venue = await BookingService.get_booking_with_related(booking_id, session)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if not venue or venue.admin_id != admin_id:
            raise HTTPException(status_code=403, detail="You don't have access to this booking")
        venue_schema = BookingVenueRead(id=venue.id, name=venue.name) if venue else None
        kourt_schema = BookingKourtRead(id=kourt.id, name=kourt.name) if kourt else None
        return BookingRead(
            id=booking.id,
            date=booking.date,
            start_time=booking.start_time.strftime('%H:%M'),
            end_time=booking.end_time.strftime('%H:%M'),
            duration_minutes=booking.duration_minutes,
            customer_name=booking.customer_name,
            customer_phone=booking.customer_phone,
            status=booking.status,
            venue=venue_schema,
            kourt=kourt_schema,
            created_at=booking.created_at.isoformat()
        )

    @staticmethod
    async def update_booking_status(booking_id, status, admin_id, session):
        """
        Updates the status of a booking managed by the admin.
        
        Args:
            booking_id: UUID of the booking.
            status: New booking status.
            admin_id: UUID of the admin user.
            session: Async database session.
        Returns:
            BookingRead: Updated booking details.
        """
        booking, kourt, venue = await BookingService.get_booking_with_related(booking_id, session)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if not venue or venue.admin_id != admin_id:
            raise HTTPException(status_code=403, detail="You don't have access to this booking")
        
        booking.status = status
        session.add(booking)
        await session.commit()
        await session.refresh(booking)
        
        venue_schema = BookingVenueRead(id=venue.id, name=venue.name) if venue else None
        kourt_schema = BookingKourtRead(id=kourt.id, name=kourt.name) if kourt else None
        return BookingRead(
            id=booking.id,
            date=booking.date,
            start_time=booking.start_time.strftime('%H:%M'),
            end_time=booking.end_time.strftime('%H:%M'),
            duration_minutes=booking.duration_minutes,
            customer_name=booking.customer_name,
            customer_phone=booking.customer_phone,
            status=booking.status,
            venue=venue_schema,
            kourt=kourt_schema,
            created_at=booking.created_at.isoformat()
        )


# Module-level functions for backward compatibility
def calculate_available_intervals(
    venue: Venue,
    kourt: Kourt,
    target_date: date,
    existing_bookings: List[Booking],
    interval_minutes: int = 30
) -> List[Dict[str, str]]:
    """Module-level wrapper for the class method."""
    return BookingService.calculate_available_intervals(
        venue, kourt, target_date, existing_bookings, interval_minutes
    )


def format_availability_response(available_intervals: List[Dict[str, str]]) -> Dict[str, any]:
    """Module-level wrapper for the class method."""
    return BookingService.format_availability_response(available_intervals)
