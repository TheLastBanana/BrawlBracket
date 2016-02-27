import uuid

class Match():
    """
    A match between two Teams in the tournament. The Tournament class will create these for you as necessary.
    """
    
    # When printing a match tree, this is the maximum length (in chars) of a seed.
    printSeedLen = 2

    def __init__(self, prereqMatches = [None, None], teams = [None, None], **kwargs):
        """
        If winnerSide is provided, teams[winnerSide] will be set as the winner.
        
        Match data:
            id: BrawlBracket id (uuid)
            nextMatch: The match to which the winner will advance (Match)
            nextMatchSide: Side of next match this leads to, i.e. self.nextMatch[self.nextMatchSide] == self (int)
            prereqMatches: The matches that lead into this one (list of Match)
            
        Tournament data:
            winner: The winning team of this match (Team)
            round: Round in the tournament (int)
        """
        self.id = kwargs.get('uuid') or uuid.uuid1()
        
        self.nextMatch = None
        self.nextMatchSide = None
        self.round = 0
        
        # Set prerequisite matches
        self.prereqMatches = prereqMatches
        
        # Set teams in this match
        self.teams = teams
            
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