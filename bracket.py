import math
from collections import deque

class Match():
    """
    A match between two Teams in the tournament. The Tournament class will create these for you as necessary.
    """
    
    # When printing a match tree, this is the maximum length (in chars) of a seed.
    printSeedLen = 2

    def __init__(self, prereqMatches = None, teams = None, winnerSide = None):
        # The next match
        self.nextMatch = None
        
        # The side of the next match this branches from (0 or 1, or None if no next match)
        self.nextMatchSide = None
    
        # The match round (inverse of depth in the graph, essentially)
        self.round = 0
        
        # The prerequisite matches
        if prereqMatches:
            self.setPrereqMatches(prereqMatches)
            
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
            
    def setPrereqMatches(self, prereqMatches):
        """
        Set the prereq matches and update them to point to this.
        """
        if len(prereqMatches) != 2:
            raise ValueError('Matches must have 2 prerequisites')
            
        self.prereqMatches = prereqMatches
        
        for side, match in enumerate(self.prereqMatches):
            if match is None:
                continue
                
            match.nextMatch = self
            match.nextMatchSide = side
            
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

class Team():
    """
    A seeded entry in the tournament. Create these through the Tournament class.
    """
    def __init__(self, seed):
        # The seed
        self.seed = seed
        
    def __repr__(self):
        return 'Team ({})'.format(self.seed)

class Tournament():
    """
    Contains all the data for a tournament. Is responsible for creation of Matches, Teams, and any other
    classes tied to a specific tournament. Also contains convenience functions for updating and getting data.
    """
    def __init__(self, teamCount = 0):
        # Set of all matches. This should only be read by outside classes.
        self.matches = set()
        
        # Set of all teams. This should only be read by outside classes.
        self.teams = set()
        
        for i in range(teamCount):
            self.createTeam(i + 1)
        
    def createTeam(self, *args):
        """
        Create a team and add it to the tournament.
        """
        team = Team(*args)
        self.teams.add(team)
        
        return team
        
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
        
    def _removeTeam(self, team):
        """
        Remove a team from the tournament.
        """
        if team not in self.teams:
            raise ValueError('Team not in tournament')
            
        self.teams.remove(team)
        
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
        
    def finalize(self):
        """
        Call this when finished creating matches. This will run any graph analysis that needs
        to be done on the matches before the tournament can be used.
        """
        return
            
    def generateMatches(self):
        """
        Generate matches fitting the number of existing teams.
        The algorithm will depend on the kind of tournament. It should always call finalize() at the end.
        """
        return
        
    def _removeMatch(self, match):
        """
        Remove a match from the tournament.
        """
        if match not in self.matches:
            raise ValueError('Match not in tournament')
            
        self.matches.remove(match)
        match._destroy()
        
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
        
    def _updateMatchRounds(self, match = None, maxDepth = None, depth = 0):
        """
        Determine the rounds for each match.
        """
        if match is None:
            if self._root is None:
                return
                
            match = self._root
        
        if maxDepth is None:
            # Subtract 1 to 0-index rounds
            maxDepth = match._getTreeDepth() - 1
            
        match.round = maxDepth - depth
        
        for prereq in match.prereqMatches:
            if prereq is None:
                continue
        
            self._updateMatchRounds(prereq, maxDepth, depth + 1)
            
    def __repr__(self):
        return self._root.prettyPrint()
        
class SingleElimTournament(TreeTournament):
    """
    A single elimintation tournament.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
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