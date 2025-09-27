from uuid import UUID
from sqlmodel import select, func
from fastapi import HTTPException
from app.models.player import Player
from app.schemas.player import PlayerCreate, PlayerUpdate, PlayerRead, PlayerListResponse

class PlayerService:
    @staticmethod
    async def create_player(player_data: PlayerCreate, session) -> PlayerRead:
        """
        Creates a new player with phone-based identification and optional email.
        Enforces uniqueness constraints for both phone and email.
        
        Args:
            player_data: Player creation data (name, phone, optional email, level, etc.)
            session: Database session
            
        Returns:
            PlayerRead: The newly created player
            
        Raises:
            HTTPException: If phone or email already exists (400)
        """
        # Check if player with same phone already exists
        existing_player = await session.exec(
            select(Player).where(Player.phone == player_data.phone)
        )
        if existing_player.first():
            raise HTTPException(
                status_code=400, 
                detail="A player with this phone number already exists"
            )
        
        # Check if player with same email already exists (if email provided)
        if player_data.email:
            existing_email = await session.exec(
                select(Player).where(Player.email == player_data.email)
            )
            if existing_email.first():
                raise HTTPException(
                    status_code=400, 
                    detail="A player with this email already exists"
                )
        
        player = Player(**player_data.model_dump())
        session.add(player)
        await session.commit()
        await session.refresh(player)
        return PlayerRead.model_validate(player)

    @staticmethod
    async def get_player(player_id: UUID, session) -> PlayerRead:
        """
        Retrieves a player by their unique ID.
        
        Args:
            player_id: UUID of the player to retrieve
            session: Database session
            
        Returns:
            PlayerRead: The requested player
            
        Raises:
            HTTPException: If player not found (404)
        """
        result = await session.exec(select(Player).where(Player.id == player_id))
        player = result.first()
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        return PlayerRead.model_validate(player)

    @staticmethod
    async def list_players(session, skip: int = 0, limit: int = 100) -> PlayerListResponse:
        """
        Lists all players with pagination support.
        
        Args:
            session: Database session
            skip: Number of records to skip for pagination (default: 0)
            limit: Maximum number of records to return (default: 100)
            
        Returns:
            PlayerListResponse: Paginated list of players with total count
        """
        count_statement = select(func.count(Player.id))
        total = await session.exec(count_statement)
        total_count = total.first()
        
        statement = select(Player).offset(skip).limit(limit)
        result = await session.exec(statement)
        players = result.all()

        player_reads = [PlayerRead.model_validate(p) for p in players]

        return PlayerListResponse(players=player_reads, total=total_count)

    @staticmethod
    async def update_player(player_id: UUID, player_data: PlayerUpdate, session) -> PlayerRead:
        """
        Updates an existing player while enforcing uniqueness constraints.
        Only provided fields will be updated (partial updates supported).
        
        Args:
            player_id: UUID of the player to update
            player_data: Updated player data (only non-null fields will be applied)
            session: Database session
            
        Returns:
            PlayerRead: The updated player
            
        Raises:
            HTTPException: If player not found (404) or constraint violations (400)
        """
        player = await PlayerService.get_player(player_id, session)
        
        # Check for phone conflicts if updating phone
        if player_data.phone and player_data.phone != player.phone:
            existing_phone = await session.exec(
                select(Player).where(Player.phone == player_data.phone, Player.id != player_id)
            )
            if existing_phone.first():
                raise HTTPException(
                    status_code=400, 
                    detail="Another player with this phone number already exists"
                )
        
        # Check for email conflicts if updating email
        if player_data.email and player_data.email != player.email:
            existing_email = await session.exec(
                select(Player).where(Player.email == player_data.email, Player.id != player_id)
            )
            if existing_email.first():
                raise HTTPException(
                    status_code=400, 
                    detail="Another player with this email already exists"
                )
        
        # Update fields
        for key, value in player_data.model_dump(exclude_unset=True).items():
            setattr(player, key, value)
        
        session.add(player)
        await session.commit()
        await session.refresh(player)
        return PlayerRead.model_validate(player)

    @staticmethod
    async def delete_player(player_id: UUID, session) -> bool:
        """
        Deletes a player if they have no active match participations.
        This prevents data integrity issues by checking relationships first.
        
        Args:
            player_id: UUID of the player to delete
            session: Database session
            
        Returns:
            bool: True if deletion was successful
            
        Raises:
            HTTPException: If player not found (404) or has active matches (400)
        """
        player = await PlayerService.get_player(player_id, session)
        
        # Check if player is in any matches (import here to avoid circular dependency)
        from app.models.matchPlayer import MatchPlayer
        match_players = await session.exec(
            select(MatchPlayer).where(MatchPlayer.player_id == player_id)
        )
        if match_players.all():
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete player who is participating in active matches"
            )
        
        await session.delete(player)
        await session.commit()
        return True

    @staticmethod
    async def find_or_create_player(phone: str, name: str, session) -> Player:
        """
        Implements the phone-first authentication strategy: finds existing player by phone
        or creates a new anonymous player for seamless social match participation.
        
        This method is crucial for the social match system - it allows users to join matches
        with just a name and phone number, without requiring full registration upfront.
        
        Args:
            phone: Player's phone number (unique identifier)
            name: Player's display name
            session: Database session
            
        Returns:
            Player: Existing player found by phone or newly created player
            
        Note:
            Returns raw Player object (not PlayerRead) for internal service use
        """
        existing_player = await session.exec(
            select(Player).where(Player.phone == phone)
        )
        existing_player_result = existing_player.first()
        if existing_player_result:
            return existing_player_result
        
        # Create new player with minimal data for quick onboarding
        player_data = PlayerCreate(name=name, phone=phone)
        created_player = await PlayerService.create_player(player_data, session)
        
        # Return raw Player object for consistency with existing player path
        result = await session.exec(select(Player).where(Player.phone == phone))
        return result.first()
