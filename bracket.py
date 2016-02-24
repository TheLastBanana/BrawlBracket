import math

class BracketNode:
    seedLen = 2

    def __init__(self):
        # The parent node to this
        self._parent = None
    
        # How deeply nested this is in the tournament (leaves are at 0)
        self._nesting = 0
        
        # The seed of the player to advance to the next round
        self._winner = None

class Match(BracketNode):
    def __init__(self, a = None, b = None, winningChild = None):
        super(Match, self).__init__()
        
        self.children = [None, None]
        self.setChild(0, a)
        self.setChild(1, b)
        
        self.winningChild = winningChild
        self.updateWinner()

    def getLines(self):
        """
        Get the lines which, if printed in sequence, make up the graphical representation
        of this node and its children.
        """
        pnSpaces = 2 ** (self._nesting - 1) - 1
        nSpaces = 2 ** (self._nesting) - 1
        
        # Length of an empty seed
        seedSpace = ' ' * BracketNode.seedLen
        
        aLines = self.getPaddedChildLines(self.children[0])
        bLines = self.getPaddedChildLines(self.children[1])
        
        winner = '{:<2}'.format(self._winner) or seedSpace
        
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
        
    def getPaddedChildLines(self, child):
        """
        Get a child node's lines, including extra padding to line up leaf nodes.
        """
        if child is None:
            lines = [' ' * BracketNode.seedLen]
        
        else:
            lines = child.getLines()
            
            # Child is not a leaf, so use its actual lines
            if child._nesting != 0:
                return lines
    
        # Child is a leaf, so we have to do some padding
        # Horizontal padding
        lines[0] = ' ' * 6 * (self._nesting - 1) + lines[0]
        
        # Vertical padding
        pnSpaces = 2 ** (self._nesting - 1) - 1
        lines = [''] * pnSpaces + lines + [''] * pnSpaces
        
        return lines
        
    def setChild(self, num, child):
        """
        Set one of the match's children.
        """
        if num < 0 or num > 1:
            raise ValueError('num must be 0 or 1')
            
        self.children[num] = child
        if child is not None:
            child.parent = self
        
        self.updateNesting()
        
    def updateNesting(self):
        """
        Update nesting to reflect children.
        """
        oldNesting = self._nesting
        
        # Treat None children as leaves
        self._nesting = max([(child._nesting if child else 0) for child in self.children]) + 1
        
        # Update parent if we changed
        if self._parent and oldNesting != self._nesting:
            self._parent.updateNesting()
            
    def updateWinner(self):
        """
        Set the winner.
        """
        oldWinner = self._winner
        if self.winningChild is None:
            # no winner yet
            self._winner = ''
        
        elif self.winningChild == 0 or self.winningChild == 1:
            # Use winning child's winner
            self._winner = self.children[self.winningChild]._winner
            
        else:
            raise ValueError('winningChild must be 0, 1, or None. Got {}'.format(self.winningChild))
            
        # Update parent if we changed
        if self._parent and oldWinner != self._winner:
            self._parent.updateWinner()
        
    def __repr__(self):
        return '\n'.join(self.getLines())

class Player(BracketNode):
    def __init__(self, seed):
        super(Player, self).__init__()
        
        self.seed = str(seed)
        self._winner = self.seed
        
    def getLines(self):
        return ['{:<2}'.format(self.seed)]


def genEmpty2nTourney(n):
    """
    Generate an empty tourney bracket for 2^n players.
    """
    if n == 0:
        return None

    tourney = Match(genEmpty2nTourney(n - 1), genEmpty2nTourney(n - 1))
        
    return tourney
    
def genTourney(n):
    """
    Generate a tourney bracket for n players and populate it with initial seeds.
    """
    nLog = math.log(n, 2)
    floorLog = math.floor(nLog)
    ceilLog = math.ceil(nLog)
    
    minPower = 2 ** floorLog
    maxPower = 2 ** ceilLog
    
    # Find the closest power of two. In a tie, pick the smallest
    nearLog = ceilLog if (maxPower - n) < (n - minPower) else floorLog
    
    tourney = genEmpty2nTourney(nearLog)
    
    return tourney

print(Match(
    Match(
        Match(
            Player(1),
            Player(2)
        ),
        Player(3)
    ),
    Match(
        Player(5),
        Player(6)
    )
))