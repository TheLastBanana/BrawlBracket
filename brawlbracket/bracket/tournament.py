import math
import uuid
from collections import deque

from .team import Team
from .match import Match
from .player import Player

class Tournament():
    """
    Contains all the data for a tournament. Is responsible for creation of Matches, Teams, and any other
    classes tied to a specific tournament. Also contains convenience functions for updating and getting data.
    """
    def __init__(self, shortName, teamCount = 0, **kwargs):
        """
        If teamCount is provided, automatically creates teamCount teams.
        
        id: BrawlBracket id (uuid)
        matches: All matches in the tournament. Read-only to outside classes. (list of Match)
        teams: All teams in the tournament. Read-only to outside classes. (list of Team)
        players: All players in the tournament. Read-only to outside classes. (list of Player)
        admins: All users that are admins for this tournament. (list of uuid)
        name: The tournament's name (string)
        shortName: The tournament's short name identifier, this is unique. (string)
        startTime: The tournament's scheduled start time. (datetime)
        checkInTime: The tournament's scheduled check in time. (datetime)
        description: The tournament's description. (string)
        style: The tournament style (e.g. single elim) (string)
        """
        self.id = kwargs.get('uuid', uuid.uuid1())
        self.name = kwargs.get('name', '')
        
        if shortName is None:
            raise ValueError('Short name can\'t be None.')
        self.shortName = shortName
        
        self.startTime = kwargs.get('startTime', None)
        self.checkInTime = kwargs.get('checkInTime', None)
        
        self.description = kwargs.get('description', '')
        self.style = 'not-set'
        
        self.matches = set()
        self.teams = set()
        self.players = set()
        
        self.admins = set()
        admin = kwargs.get('admin')
        if admin is not None:
            self.admins.add(admin)
        
        for i in range(teamCount):
            self.createTeam(i + 1)
        
    def createTeam(self, *args, **kwargs):
        """
        Create a team and add it to the tournament.
        """
        team = Team(*args, **kwargs)
        self.teams.add(team)
        
        return team
        
    def createMatch(self, *args, **kwargs):
        """
        Create a match and add it to the tournament.
        """
        if len(args) > 0 and args[0]:
            for match in args[0]:
                if match is None: continue
                if match not in self.matches:
                    raise ValueError('Match not in tournament')
                    
        if len(args) > 1 and args[1]:
            for team in args[1]:
                if team is None: continue
                if team not in self.teams:
                    raise ValueError('Team not in tournament')
        
        match = Match(*args, **kwargs)
        self.matches.add(match)
        
        return match
        
    def createPlayer(self, *args, **kwargs):
        """
        Create a player and add it to the tournament.
        """
        player = Player(*args, **kwargs)
        self.players.add(player)
        
        return player
        
    def reset(self):
        """
        Reset the tournament back to starting state.
        """
        for match in self.matches:
            match.winner = None
            
            for side, prereq in enumerate(match.prereqMatches):
                # Clear team if this isn't the team's first match
                if prereq is not None:
                    match.teams[side] = None
        
    def finalize(self):
        """
        Call this when finished creating matches. This will run any graph analysis that needs
        to be done on the matches before the tournament can be used.
        """
        # Finalize matches
        for m in self.matches:
            m.finalize()
        
        return
            
    def generateMatches(self):
        """
        Generate matches fitting the number of existing teams.
        The algorithm will depend on the kind of tournament. It should always call finalize() at the end.
        """
        return
        
    def _removeTeam(self, team):
        """
        Remove a team from the tournament.
        """
        if team not in self.teams:
            raise ValueError('Team not in tournament')
            
        self.teams.remove(team)
        
    def _removeMatch(self, match):
        """
        Remove a match from the tournament.
        """
        if match not in self.matches:
            raise ValueError('Match not in tournament')
            
        self.matches.remove(match)
        match._destroy()
        
    def getUserInfo(self, user):
        """
        Get info relevant to a user. This is the user's match, team, and player.
        
        Returns (Match, Team, Player) if user is in tournament.
        Returns None otherwise.
        """
        for m in self.matches:
            # We want an active game, not one that's already done
            if m.winner is not None:
                continue
            
            for t in m.teams:
                # Team not set yet
                if t is None:
                    continue
                
                for p in t.players:
                    if p.user.id == user.id:
                        return (m, t, p)
        
        return None
        
    def getDisplayJSON(self):
        """
        Get the JSON data for use in client-side bracket display.
        """
        teamsData = {}
        for team in self.teams:
            teamsData[str(team.id)] = {
                'name': team.name or 'Unnamed Team'
            }
            
        matchesData = {}
        for match in self.matches:
            matchesData[str(match.id)] = {
                'id': match.number,
                'teams': [team.id if team else None for team in match.teams],
                'prereqMatches': [prereq.id if prereq else None for prereq in match.prereqMatches],
                'score': match.score,
                'winner': match.winner or None
            }
        
        return {
            'teams': teamsData,
            'matches': matchesData,
            'root': self.root.id if self.root else None
        }
        
class TreeTournament(Tournament):
    """
    A tournament that follows a tree structure (with each match leading into the next).
    """
    def __init__(self, *args, **kwargs):
        # Root match
        self._root = None
        
        super().__init__(*args, **kwargs)
        
    @property
    def root(self):
        """
        The root (usually final) match.
        """
        return self._root
        
    @root.setter
    def root(self, match):
        if match not in self.matches:
            raise ValueError('Match not in tournament')
        
        self._root = match
        
    def finalize(self):
        """
        Update rounds starting from the root match.
        """
        self._updateMatchRounds()
        self._numberMatches()
        
        # Super class finalize
        Tournament.finalize(self)
        
    def _updateMatchRounds(self, root = None, maxDepth = None, depth = 0):
        """
        Determine the rounds for each match.
        """
        if root is None:
            if self._root is None:
                return
                
            root = self._root
        
        if maxDepth is None:
            # Subtract 1 to 0-index rounds
            maxDepth = root._getTreeDepth() - 1
            
        root.round = maxDepth - depth
        
        for prereq in root.prereqMatches:
            if prereq is None:
                continue
        
            self._updateMatchRounds(prereq, maxDepth, depth + 1)
            
    def _numberMatches(self, root = None, start = 1):
        if root is None:
            if self._root is None:
                return
                
            root = self._root
            
        traversed = []
        toVisit = deque([root])
        
        # Traverse matches from highest to lowest level of tree
        while toVisit:
            match = toVisit.popleft()
            traversed.append(match)
            
            # In reverse so side 0 comes before side 1 when we reverse again later
            for prereq in reversed(match.prereqMatches):
                if prereq:
                    toVisit.append(prereq)
                    
        # Number from lowest to highest in tree
        for match in reversed(traversed):
            match.number = start
            start += 1
        
            
    def __repr__(self):
        return self._root.prettyPrint()
        
class SingleElimTournament(TreeTournament):
    """
    A single elimintation tournament.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = 'Single Elimination'
    
    def generateMatches(self):
        n = len(self.teams)
        
        if (n < 2):
            return
        
        logN = math.log(n, 2)
        ceilLog = math.ceil(logN)
        
        # Nearest power of two
        highPo2 = 2 ** ceilLog
        
        # Generate symmetric tree
        matchesByRound = []
        self._root = self._genMatchTree(ceilLog, matchesByRound)
        
        # Number of byes needed
        numByes = highPo2 - n
        
        # List of teams sorted by seed
        teamsToAssign = list(self.teams)
        teamsToAssign.sort(key=lambda team: team.seed)
        
        # Add None to represent byes
        teamsToAssign += [None] * numByes
        
        # To build the tournament, predict the winner (based on seed) for each match starting from the final match
        # Final prediction should be our lowest seed
        self._root.winner = teamsToAssign[0]
        
        # Work down from final round
        matchesByRound.reverse()
        for roundMatches in matchesByRound[:-1]:
            # Sort matches by predicted winners and determine which teams need to be assigned
            sortedMatches, roundTeams = self.__roundData(roundMatches, teamsToAssign)
        
            for match in sortedMatches:
                # Propagate predicted winner to next level
                match.prereqMatches[0].winner = match.winner
                
                # Expected loser is lowest seed in the teams available for this round
                match.prereqMatches[1].winner = roundTeams.pop()
        
        # For the first round, add the predicted winners as actual playing teams
        sortedMatches, roundTeams = self.__roundData(matchesByRound[-1], teamsToAssign)
        for match in sortedMatches:
            loser = roundTeams.pop()
            
            # This team will be playing its first match in the second round, so remove this match
            if loser is None:
                match.nextMatch.teams[match.nextMatchSide] = match.winner
                self._removeMatch(match)
                
            else:
                match.teams[0] = match.winner
                match.teams[1] = loser
                
        # Clear predicted winners
        self.reset()
        
        self.finalize()
        
    def _genMatchTree(self, rounds, matchesByRound, maxRounds = None):
        """
        Generate a symmetric match tree with the given number of rounds (2^rounds matches).
        """
        # First call, so set the max rounds
        if maxRounds is None:
            maxRounds = rounds
            
            # Create an empty list of matches for each of the rounds
            for i in range(rounds):
                matchesByRound.append([])
        
        # First round has no children
        if rounds == 1:
            match = self.createMatch()

        # Recurse to next round
        else:
            match = self.createMatch([
                self._genMatchTree(rounds - 1, matchesByRound, maxRounds),
                self._genMatchTree(rounds - 1, matchesByRound, maxRounds)
            ])
        
        # Add this match to the list of matches in the current round
        matchesByRound[rounds - 1].append(match)
        
        return match
        
    def __roundData(self, matches, teams):
        """
        Internal function to gather data about a round.
        """
        matches.sort(key=lambda match: match.winner.seed)
        numMatches = len(matches)
        
        # Teams to be assigned in this round
        # We already assigned numMatches in the previous rounds, and there are numMatches matches in the round,
        # so we pick the first remaining numMatches teams
        roundTeams = teams[numMatches:numMatches*2]
        
        return (matches, roundTeams)