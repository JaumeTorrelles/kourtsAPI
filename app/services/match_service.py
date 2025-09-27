from uuid import UUID
from datetime import date, time
from sqlmodel import select
from fastapi import HTTPException
from app.models.match import Match
from app.models.matchPlayer import MatchPlayer
from app.models.player import Player
from app.schemas.match import MatchRead, MatchListResponse, MatchPlayerRead, MatchStatus, MatchActionResponse
from app.services.player_service import PlayerService

class MatchService:
    @staticmethod
    async def create_match(creator_name: str, creator_phone: str, date: date, start_time: time, end_time: time, max_players: int, session) -> MatchActionResponse:
        """
        Creates a new social match with the creator as the first player.
        
        Args:
            creator_name: Name of the player creating the match
            creator_phone: Phone number of the creator (used for identification)
            date: Date when the match will take place
            start_time: Match start time
            end_time: Match end time
            max_players: Maximum number of players allowed in the match
            session: Database session
            
        Returns:
            MatchActionResponse: Success message with match ID
            
        Raises:
            HTTPException: If validation fails (min players, invalid times)
        """
        if max_players < 2:
            raise HTTPException(status_code=400, detail="Match must have at least 2 players")
        if start_time >= end_time:
            raise HTTPException(status_code=400, detail="Start time must be before end time")
        
        # Automatically find or create the player
        creator = await PlayerService.find_or_create_player(creator_phone, creator_name, session)
        
        match = Match(
            creator_id=creator.id,
            date=date,
            start_time=start_time,
            end_time=end_time,
            max_players=max_players,
            num_players=1,
            status=MatchStatus.OPEN.value
        )
        session.add(match)
        await session.commit()
        await session.refresh(match)
        match_player = MatchPlayer(match_id=match.id, player_id=creator.id)
        session.add(match_player)
        await session.commit()
        return MatchActionResponse(message="Match created successfully", match_id=match.id)

    @staticmethod
    async def list_matches(session):
        """
        Lists all open matches with their players. Optimized to avoid N+1 queries.
        
        Args:
            session: Database session
            
        Returns:
            MatchListResponse: List of open matches with player details
        """
        result = await session.exec(select(Match).where(Match.status == "Open"))
        matches = result.all()
        
        # Optimize: Get all match players and players in batch to avoid N+1 queries
        match_ids = [m.id for m in matches]
        if not match_ids:
            return MatchListResponse(matches=[])
            
        # Get all match-player relationships for these matches
        mp_result = await session.exec(
            select(MatchPlayer, Player)
            .join(Player, MatchPlayer.player_id == Player.id)
            .where(MatchPlayer.match_id.in_(match_ids))
        )
        match_player_data = mp_result.all()
        
        # Group players by match_id
        players_by_match = {}
        for mp, player in match_player_data:
            if mp.match_id not in players_by_match:
                players_by_match[mp.match_id] = []
            players_by_match[mp.match_id].append(
                MatchPlayerRead(id=player.id, name=player.name, level=player.level)
            )
        
        # Build match responses
        match_responses = []
        for m in matches:
            players = players_by_match.get(m.id, [])
            match_responses.append(MatchRead(
                id=m.id,
                date=m.date,
                start_time=m.start_time,
                end_time=m.end_time,
                max_players=m.max_players,
                num_players=m.num_players,
                status=MatchStatus(m.status),
                players=players,
                created_at=m.created_at
            ))
        return MatchListResponse(matches=match_responses)

    @staticmethod
    async def join_match(match_id: UUID, player_name: str, player_phone: str, session) -> MatchActionResponse:
        """
        Adds a player to an existing open match.
        
        Args:
            match_id: ID of the match to join
            player_name: Name of the joining player
            player_phone: Phone number of the joining player
            session: Database session
            
        Returns:
            MatchActionResponse: Success message with match ID
            
        Raises:
            HTTPException: If match not found, closed, full, or player already joined
        """
        result = await session.exec(select(Match).where(Match.id == match_id))
        match = result.first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        if match.status != "Open":
            raise HTTPException(status_code=400, detail="Match is not open for new players")
        if match.num_players >= match.max_players:
            raise HTTPException(status_code=400, detail="Match is already full")
        
        # Automatically find or create the player
        player = await PlayerService.find_or_create_player(player_phone, player_name, session)
        
        result = await session.exec(select(MatchPlayer).where(MatchPlayer.match_id == match_id, MatchPlayer.player_id == player.id))
        if result.first():
            raise HTTPException(status_code=400, detail="Player is already in this match")
        match_player = MatchPlayer(match_id=match_id, player_id=player.id)
        session.add(match_player)
        match.num_players += 1
        session.add(match)
        await session.commit()
        return MatchActionResponse(message="Player joined match successfully", match_id=match.id)

    @staticmethod
    async def get_match_details(match_id: UUID, session):
        """
        Gets detailed information about a specific match including all players.
        Optimized to avoid N+1 queries.
        
        Args:
            match_id: ID of the match to retrieve
            session: Database session
            
        Returns:
            MatchRead: Complete match details with player list
            
        Raises:
            HTTPException: If match not found
        """
        result = await session.exec(select(Match).where(Match.id == match_id))
        match = result.first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
            
        # Optimize: Get players with JOIN to avoid N+1 queries
        result = await session.exec(
            select(MatchPlayer, Player)
            .join(Player, MatchPlayer.player_id == Player.id)
            .where(MatchPlayer.match_id == match_id)
        )
        match_player_data = result.all()
        
        players = [
            MatchPlayerRead(id=player.id, name=player.name, level=player.level)
            for _, player in match_player_data
        ]
        return MatchRead(
            id=match.id,
            date=match.date,
            start_time=match.start_time,
            end_time=match.end_time,
            max_players=match.max_players,
            num_players=match.num_players,
            status=MatchStatus(match.status),
            players=players,
            created_at=match.created_at
        )

    @staticmethod
    async def leave_match(match_id: UUID, player_phone: str, session) -> MatchActionResponse:
        """
        Removes a player from a match. If the creator leaves and other players remain,
        the operation is blocked. If it's the last player, the match is deleted.
        
        Args:
            match_id: ID of the match to leave
            player_phone: Phone number of the player leaving
            session: Database session
            
        Returns:
            MatchActionResponse: Success message with match ID
            
        Raises:
            HTTPException: If match/player not found, player not in match, or creator restriction
        """
        result = await session.exec(select(Match).where(Match.id == match_id))
        match = result.first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        # Find player by phone
        result = await session.exec(select(Player).where(Player.phone == player_phone))
        player = result.first()
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        result = await session.exec(select(MatchPlayer).where(MatchPlayer.match_id == match_id, MatchPlayer.player_id == player.id))
        match_player = result.first()
        if not match_player:
            raise HTTPException(status_code=400, detail="Player is not in this match")
        
        if match.creator_id == player.id and match.num_players > 1:
            raise HTTPException(status_code=400, detail="Match creator cannot leave while other players remain")
        
        await session.delete(match_player)
        match.num_players -= 1
        if match.num_players == 0:
            await session.delete(match)
        else:
            session.add(match)
        await session.commit()
        return MatchActionResponse(message="Player left match successfully", match_id=match.id)
