import uuid
from brawlbracket import chatmanager

class Match():
    """
    A match between two Teams in the tournament. The Tournament class will create these for you as necessary.
    """
    
    # When printing a match tree, this is the maximum length (in chars) of a seed.
    printSeedLen = 2

    def __init__(self, prereqMatches = None, teams = None, **kwargs):
        """
        If winnerSide is provided, teams[winnerSide] will be set as the winner.
        
        Match data:
            id: BrawlBracket id (uuid)
            nextMatch: The match to which the winner will advance (Match)
            nextMatchSide: Side of next match this leads to, i.e. self.nextMatch[self.nextMatchSide] == self (int)
            prereqMatches: The matches that lead into this one (list of Match)
            chat: The chat log (Chat)
            score: Team scores, team index 0 is score index 0 (list of int)
            teams: Teams participating in this match (list of Team)
            realmBans: Which realms are currently banned (list of string id)
            startTime: When this match started (date)
            roomNumber: Brawlhalla custom room number (int)
            currentRealm: Current realm being played (string id)
            banRule: The method of determining bans and picks (BanRule)
            state: The state of the match
            
        Tournament data:
            winner: The winning team of this match, None if no winner yet (Team)
            round: Round in the tournament (int)
            number: The number of the match in the tournament. Roughly the order they'll be played in. (int)
            bestOf: Maximum number of games in this match (int)
        
        Properties (read only accessor):
            lobbyStatus: Returns tuple of lobby status. (string, string, int)
        """
        self.id = kwargs.get('uuid', uuid.uuid1())
        
        self.nextMatch = None
        self.nextMatchSide = None
        self.round = 0
        self.number = 0
        
        # Set prerequisite matches
        if prereqMatches is None:
            self.prereqMatches = [None, None]
        else:
            self.prereqMatches = prereqMatches
        
        # Set teams in this match
        if teams is None:
            self.teams = [None, None]
        else:
            self.teams = teams
        
        # Generate a new chat room
        self.chat = kwargs.get('chat')
        if self.chat is None:
            self.chat = chatmanager.createChat()
        
        self.score = [0, 0]
        
        # Set to None to begin with, this should be set later
        self.bestOf = None
        
        self.winner = None
        
        self.state = {}
        self.state['name'] = 'building'
        
        self.realmBans = []
        self.startTime = None
        self.roomNumber = None
        self.currentRealm = None
        self.banRule = None
                        
    @property
    def prereqMatches(self):
        return self._prereqMatches
            
    @prereqMatches.setter
    def prereqMatches(self, matches):
        """
        Set the prereq matches and update them to point to this.
        """
        if len(matches) != 2:
            raise ValueError('Matches must have 2 prerequisites')
            
        self._prereqMatches = matches
        
        for side, match in enumerate(self._prereqMatches):
            if match is None:
                continue
                
            match.nextMatch = self
            match.nextMatchSide = side
        
    def _getTreeDepth(self):
        """
        Get the maximum depth of the match tree.
        """
        return max([(match._getTreeDepth() if match else 0) for match in self.prereqMatches]) + 1

    def _getDisplayLines(self):
        """
        Get the lines which, if printed in sequence, make up the graphical representation
        of this node and its children.
        """
        pnSpaces = 2 ** self.round - 1
        nSpaces = 2 ** (self.round + 1) - 1
        
        # Length of an empty seed
        seedSpace = ' ' * Match.printSeedLen
        
        aLines = self._getChildDisplayLines(0)
        bLines = self._getChildDisplayLines(1)
        
        # Combine previous lines vertically, adding a space between them
        combined = aLines + [''] + bLines
        
        # Pad line lengths
        childLen = max(len(line) for line in combined)
        for i in range(len(combined)):
            combined[i] = ('{:<' + str(childLen) + '}').format(combined[i])
        
        # Add team seeds and corners
        seeds = []
        seedFormat = '{:<' + str(Match.printSeedLen) + '}'
        for team in self.teams:
            if team:
                seeds.append(seedFormat.format(team.seed))
                
            else:
                seeds.append(seedSpace)
        
        combined[pnSpaces] += seeds[0] + '─┐'
        combined[-pnSpaces - 1] += seeds[1] + '─┘'
        
        for i in range(pnSpaces + 1, len(combined) - pnSpaces - 1):
            # Connector for center piece
            if i == nSpaces:
                combined[i] += seedSpace + ' ├─'
                
            # Connecting bars for every other line between corners
            else:
                combined[i] += seedSpace + ' │'
        
        return combined
        
    def _getChildDisplayLines(self, side):
        """
        Get a child node's lines, including extra padding to line up leaf nodes.
        """
        if self.prereqMatches[side]:
            # Get match lines
            lines = self.prereqMatches[side]._getDisplayLines()
            
            return lines
            
        elif self.round > 0:
            # Each match is 6 characters wide plus seed length
            hSpace = 5 * self.round
            
            # Leaf nodes are 3 wide, and this grows exponentially
            vSpace = 2 ** self.round + 1
            
            return [' ' * hSpace] * vSpace
            
        else:
            return ['']
            
    def _destroy(self):
        """
        Unlink the match from other matches.
        """
        if self.nextMatch:
            nextPrereqs = self.nextMatch.prereqMatches
            side = nextPrereqs.index(self)
            nextPrereqs[side] = None
            
        for match in self.prereqMatches:
            if match is None:
                continue
            
            match.nextMatch = None
        
    def prettyPrint(self):
        """
        Print the match out as a tree structure.
        """
        return '\n'.join(self._getDisplayLines())
    
    def finalize(self):
        """
        Finalize this match. Should be able to confidently update state now.
        """
        self._updateState()
    
    def getLobbyData(self):
        """
        Get data relevant to the lobby.
        See https://github.com/TheLastBanana/BrawlBracket/wiki/JSON-objects
        for listing.
        """
        lobbyData = {}
        
        lobbyData['number'] = self.number
        lobbyData['state'] = self.state
        lobbyData['chatId'] = str(self.chat.id)
        lobbyData['realmBans'] = self.realmBans
        lobbyData['bestOf'] = self.bestOf
        lobbyData['startTime'] = self.startTime
        lobbyData['roomNumber'] = self.roomNumber
        lobbyData['currentRealm'] = self.currentRealm
        
        lobbyData['teams'] = []
        lobbyData['players'] = []
        for t, wins in zip(self.teams, self.score):
            if t is None:
                continue
            
            team = {}
            team['name'] = t.name
            team['id'] = str(t.id)
            team['seed'] = t.seed
            team['ready'] = False not in [p.online for p in t.players]
            team['wins'] = wins
            team['avatar'] = t.players[0].user.avatar
            lobbyData['teams'].append(team)
            
            for p in t.players:
                player = {}
                player['name'] = p.user.username
                player['status'] = 'Online' if p.online else 'Offline'
                player['legend'] = 'none'
                lobbyData['players'].append(player)
        
        return lobbyData
    
    def _updateState(self):
        """
        Updates this Match's state.
        """
        for m in self.prereqMatches:
            # No prereq
            if m is None:
                continue
                
            # Match isn't done
            if m.winner is None:
                self.state.clear()
                self.state['name'] = 'waitingForMatch'
                self.state['teamNames'] = [x.name for x in m.teams
                                            if x is not None]
                self.state['matchNumber'] = m.number
                return
        
        for team in self.teams:
            # No team yet
            for player in team.players:
                if not player.online:
                    self.state.clear()
                    self.state['name'] = 'waitingForPlayers'
                    return
    
    @property
    def lobbyStatus(self):
        """
        Lobby status.
        
        Returns (name, pretty name, sort order)
        """
        stateName = self.state['name']
        if stateName == 'waitingForMatch':
            prereqMatch = None
            for m in self.prereqMatches:
                if m is None:
                    continue
                elif m.winner is None:
                    prereqMatch = m
                    break
            # Didn't find prereqMatch
            else:
                raise AssertionError(
                    'Waiting for match but no prereq match. {}'
                        .format(self.id)
                    )
            
            return (stateName,
                    'Waiting for match #{}'.format(prereqMatch.number),
                    # Higher priority if one team is done, but still lower than
                    # if both are (i.e. waitingForPlayers)
                    5 if self.teams.count(None) <= 1 else 6)
            
        elif stateName == 'waitingForPlayers':
            # Show team names -- all player names in e.g. 2v2s would make a really long string
            notReady = []
            for team in self.teams:
                if not all([p.online for p in team.players]):
                    notReady.append(team.name)
            
            # We assume there are only 2 participants in a lobby
            if len(notReady) == 2:
                return (stateName,
                        'Waiting for both teams',
                        # Both teams inactive, so lower priority than if one is
                        # team active
                        4)
            
            return (stateName,
                    'Waiting for {}'.format(notReady[0]),
                    # One team inactive, so lower priority than if both are active
                    3)
                    
        elif stateName == 'complete':
            return (stateName,
                    'Complete',
                    # Completed matches have low priority
                    7)
                
        return ('unknown', 'Unknown', 98)
