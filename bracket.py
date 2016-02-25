import math

class Match():
    """
    A match between two Teams in the tournament.
    """
    
    printSeedLen = 2

    def __init__(self, prereqMatches = None, teams = None, winnerSide = None):
        # The next match
        self.nextMatch = None
    
        # The match round (inverse of depth in the graph, essentially)
        self.round = 0
        
        # The prerequisite matches
        if prereqMatches:
            if len(prereqMatches) != 2:
                raise ValueError('Matches must have 2 prerequisites')
            
            self.prereqMatches = prereqMatches
            
            for match in self.prereqMatches:
                if match is None:
                    continue
                    
                match.nextMatch = self
            
        else:
            self.prereqMatches = [None, None]
        
        # The teams in this match
        if teams:
            if len(teams) != 2:
                raise ValueError('Matches must have 2 teams')
            
            self.teams = [None, None]
            for i, team in enumerate(teams):
                # No team, so try to get the previous match's winner
                if team is None:
                    self._updateTeamFromPrereq(i)
                
                else:
                    self.teams[i] = team
            
        else:
            # Take winners from previous matches
            self._updateTeamsFromPrereqs()
        
        # Winning team
        if winnerSide is None:
            self.winner = None
            
        else:
            self.winner = self.teams[winnerSide]
            
    def _updateTeamsFromPrereqs(self):
        """
        Update all teams based on the prerequisite matches' winners.
        """
        self.teams = [(match.winner if match else None) for match in self.prereqMatches]
        
    def _updateTeamFromPrereq(self, side):
        """
        Update a side's team based on the prerequisite match's winners.
        """
        if self.prereqMatches[side]:
            self.teams[side] = self.prereqMatches[side].winner
        else:
            self.teams[side] = None
        
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
        
        if self.winner:
            winner = ('{:<' + str(Match.printSeedLen) + '}').format(self.winner.seed)
        else:
            winner = seedSpace
        
        # Combine previous lines vertically, adding a space between them
        combined = aLines + [''] + bLines
        
        # Pad line lengths
        childLen = max(len(line) for line in combined)
        for i in range(len(combined)):
            combined[i] = ('{:<' + str(childLen) + '}').format(combined[i])
        
        # Add corners
        combined[pnSpaces] += '─┐' + seedSpace
        combined[-pnSpaces - 1] += '─┘' + seedSpace
        
        for i in range(pnSpaces + 1, len(combined) - pnSpaces - 1):
            # Connector for center piece
            if i == nSpaces:
                combined[i] += ' ├─ ' + winner
                
            # Connecting bars for every other line between corners
            else:
                combined[i] += ' │' + seedSpace
        
        return combined
        
    def _getChildDisplayLines(self, side):
        """
        Get a child node's lines, including extra padding to line up leaf nodes.
        """
        if self.prereqMatches[side]:
            # Get match lines
            lines = self.prereqMatches[side]._getDisplayLines()
            
            return lines
            
        else:
            # Child is a leaf, so we have to do some padding
            if self.teams[side]:
                # Get team seed
                seed = self.teams[side].seed
                lines = [('{:<' + str(Match.printSeedLen) + '}').format(seed)]
            
            else:
                lines = [' ' * Match.printSeedLen]
                
    
            # Horizontal padding
            lines[0] = ' ' * 6 * self.round + lines[0]
            
            # Vertical padding
            pnSpaces = 2 ** self.round - 1
            lines = [''] * pnSpaces + lines + [''] * pnSpaces
            
            return lines
        
    def __repr__(self):
        return '\n'.join(self._getDisplayLines())

class Team():
    """
    A seeded entry in the tournament.
    """
    def __init__(self, seed):
        # The seed
        self.seed = str(seed)
        
    def __repr__(self):
        return self.seed

class Tournament():
    """
    Contains all the data for a tournament. Is responsible for creation of Matches, Teams, and any other
    classes tied to a specific tournament. Also contains convenience functions for updating and getting data.
    """
    def __init__(self):
        # Set of all matches
        self.matches = set()
        
        # Set of all teams
        self.teams = set()
        
        # Last match created
        self.lastMatch = None
        
    def createMatch(self, *args):
        """
        Create a match and add it to the tournament.
        """
        if args[0]:
            for match in args[0]:
                if match is None: continue
                if match not in self.matches:
                    raise ValueError('Match not in tournament')
                    
        if args[1]:
            for team in args[1]:
                if team is None: continue
                if team not in self.teams:
                    raise ValueError('Team not in tournament')
        
        match = Match(*args)
        self.matches.add(match)
        
        self.lastMatch = match
        
        return match
        
    def createTeam(self, *args):
        """
        Create a team and add it to the tournament.
        """
        team = Team(*args)
        self.teams.add(team)
        
        return team
        
    def updateMatchRounds(self, match = None, maxDepth = None, depth = 0):
        """
        Determine the rounds for each match.
        """
        if match is None:
            match = self.lastMatch
        
        if maxDepth is None:
            # Subtract 1 to 0-index rounds
            maxDepth = match._getTreeDepth() - 1
            
        match.round = maxDepth - depth
        
        for prereq in match.prereqMatches:
            if prereq is None:
                continue
        
            self.updateMatchRounds(prereq, maxDepth, depth + 1)
            
        
    def __repr__(self):
        return str(self.lastMatch)

# def genEmpty2nTourney(n):
    # """
    # Generate an empty tourney bracket for 2^n players.
    # """
    # if n == 0:
        # return None

    # tourney = Match(genEmpty2nTourney(n - 1), genEmpty2nTourney(n - 1))
        
    # return tourney
    
# def genTourney(n):
    # """
    # Generate a tourney bracket for n players and populate it with initial seeds.
    # """
    # nLog = math.log(n, 2)
    # floorLog = math.floor(nLog)
    # ceilLog = math.ceil(nLog)
    
    # minPower = 2 ** floorLog
    # maxPower = 2 ** ceilLog
    
    # # Find the closest power of two. In a tie, pick the smallest
    # nearLog = ceilLog if (maxPower - n) < (n - minPower) else floorLog
    
    # tourney = genEmpty2nTourney(nearLog)
    
    # return tourney
    
t1 = Tournament()
t1.createMatch(
    [
        t1.createMatch(
            None,
            [t1.createTeam(1), t1.createTeam(2)],
            1
        ),
        
        t1.createMatch(
            None,
            [t1.createTeam(3), t1.createTeam(4)],
            0
        )
    ],
    None,
    0
)
t1.updateMatchRounds()
    
t2 = Tournament()
t2.createMatch(
    [
        t2.createMatch(
            None,
            [t2.createTeam(1), t2.createTeam(2)],
            1
        ),
        None
    ],
    [
        None,
        t2.createTeam(3)
    ],
    0
)
t2.updateMatchRounds()
    
t3 = Tournament()
t3.createMatch(
    [
        t3.createMatch(
            [
                t3.createMatch(
                    None,
                    [t3.createTeam(1), t3.createTeam(2)],
                    1
                ),
                None
            ],
            [
                None,
                t3.createTeam(3)
            ],
            0
        ),
        
        None
    ],
    [None, t3.createTeam(4)],
    1
)
t3.updateMatchRounds()

print(t1)
print()
print(t2)
print()
print(t3)