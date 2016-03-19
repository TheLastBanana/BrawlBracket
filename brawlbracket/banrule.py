from brawlbracket import util

class BanRule:
    """
    Class that handles ban and pick orders for matches.
    """
    def __init__(self):
        pass
        
    def advanceState(self, match):
        """
        Handles all of the logic of what the next state should be.
        Generic implementation naively checks state name and hands off to a
        sub function.
        
        State order:
            - waitingForPlayers
            - pickLegends
            - chooseMap
            - createRoom
        
        Directly modifies match.state.
        """
        state = match.state
        # Entry point into the cyclic states, straight to pickLegends
        if state['name'] == 'waitingForPlayers':
            state.clear()
            state['name'] = 'pickLegends'
        
        while True:
            if state['name'] == 'pickLegends':
                self._getNextLegendStep(match)
            
            if state['name'] == 'chooseMap':
                self._getNextMapStep(match)
            
            if state['name'] == 'createRoom':
                self._getNextRoomStep(match)
            
            if state['name'] == 'inGame':
                if self._getNextGameStep(match):
                    continue
            break
    
    def _getNextLegendStep(self, match):
        """
        Intended to determine the next step in the legend picking process.
        This could be the next person to pick or ban.
        """
        raise NotImplementedError('No generic getNextLegendStep')
    
    def _getNextMapStep(self, match):
        """
        Intended to determine the next step in the realm picking process.
        This could be the next person to pick or ban.
        """
        raise NotImplementedError('No generic getNextMapStep')
    
    def _getNextRoomStep(self, match):
        """
        Intended to determine the next step in the room picking process.
        Generic implementation checks to see if room is set, if it isn't
        then it passes. If it is then it advances to the inGame state.
        """
        if match.roomNumber is not None:
            state = match.state
            state.clear()
            state['name'] = 'inGame'
    
    def _getNextGameStep(self, match):
        """
        Intended to determine the next step in the in game process.
        
        Returns True if the state update process should be restarted.
        """
        state = match.state
        realGameNumber = sum(match.score)
        currentGameNumber = match.currentGameNumber
        
        # Error
        if currentGameNumber > realGameNumber:
            raise AssertionError('currentGameNumber ahead of realGameNumber.')
        # Nothing to do
        elif currentGameNumber == realGameNumber:
            return
        # Game done, update
        else:
            # Match done move forwards
            if max(match.score) > (match.bestOf // 2):
                # TODO: Make this move people to next match and eliminate others
                return false
            else:
                # Reset things to pregame state
                match.clearRealmsBans()
                match.currentRealm = None
                for team in match.teams:
                    for player in team.players:
                        player.currentLegend = None
                
                state.clear()
                state['name'] = 'pickLegend'
                
                return True

class BasicRules(BanRule):
    """
    A basic implementation of rules.
    """     
    # override
    def _getNextLegendStep(self, match):
        """
        Basic picking order. Higher seed
        """
        state = match.state
        
        teams = list(match.teams)
        teams.sort(key = lambda t: t.seed, reverse = True)
        
        userIds = None
        if any(p.currentLegend is None for p in teams[0].players):
            userIds = [str(p.user.id) for p in teams[0].players
                            if p.currentLegend is None]
        elif any(p.currentLegend is None for p in teams[1].players):
            userIds = [str(p.user.id) for p in teams[1].players
                            if p.currentLegend is None]
        # We're done picking, advance.
        else:
            state.clear()
            match.state['name'] = 'chooseMap'
            return
        
        state.clear()
        state['name'] = 'pickLegends'
        match.state['canPick'] = userIds
    
    def _getNextMapStep(self, match):
        """
        Basic pick ban order.
        """
        currentBans = match.getRealmBans()
        state = match.state
        # Ban up until 2 maps left
        if len(currentBans) < (len(util.eslRealms) - 2):
            state.clear()
            state['name'] = 'chooseMap'
            
            # Player 0 == captain
            state['turn'] = str(match.teams[len(currentBans)%2]\
                                .players[0].user.id)
            state['action'] = 'ban'
        elif match.currentRealm is None:
            state.clear()
            state['name'] = 'chooseMap'
            
            # Player 0 == captain
            state['turn'] = str(match.teams[len(currentBans)%2]\
                                .players[0].user.id)
            state['action'] = 'pick'
        else:
            state.clear()
            state['name'] = 'createRoom'

class ESLRules(BanRule):
    """
    Rules for ESL style tournaments
    """
            
    # override
    def _getNextLegendStep(self, match):
        """
        Basic picking order. Higher seed picks first.
        
        This is NOT ESL rules yet.
        """
        state = match.state
        
        teams = list(match.teams)
        teams.sort(key = lambda t: t.seed, reverse = True)
        
        userIds = None
        if any(p.currentLegend is None for p in teams[0].players):
            userIds = [str(p.user.id) for p in teams[0].players
                            if p.currentLegend is None]
        elif any(p.currentLegend is None for p in teams[1].players):
            userIds = [str(p.user.id) for p in teams[1].players
                            if p.currentLegend is None]
        # We're done picking, advance.
        else:
            state.clear()
            match.state['name'] = 'chooseMap'
            return
        
        state.clear()
        state['name'] = 'pickLegends'
        match.state['canPick'] = userIds
    
    def _getNextMapStep(self, match):
        """
        First game players ban until one realm is left. Subsequent games
        higher seed bans two maps and low seed picks from remaining.
        """
        currentBans = match.getRealmBans()
        state = match.state
        gameNumber = sum(match.score)
        
        # First game of match
        if gameNumber == 0:
            # Ban up until one realm left
            if len(currentBans) < (len(util.eslRealms) - 1):
                state.clear()
                state['name'] = 'chooseMap'
                state['action'] = 'ban'
                
                # Player 0 == captain
                state['turn'] = str(match.teams[len(currentBans)%2]\
                                    .players[0].user.id)
            # Auto pick the last realm
            elif match.currentRealm is None:
                state.clear()
                state['name'] = 'chooseMap'
                
                for realm in util.eslRealms:
                    if realm not in currentBans:
                        match.currentRealm = realm
                        break
                else:
                    raise AssertionError('Only one realm left but couldn\'t '
                                         'find it.')
            # Advance to next state
            else:
                state.clear()
                state['name'] = 'createRoom'
        # After first game
        else:
            # Ban up to two realms
            if len(currentBans) < 2:
                highestSeed = max(match.teams, key=lambda t: t.seed)
                
                state.clear()
                state['name'] = 'chooseMap'
                state['action'] = 'ban'
                state['turn'] = str(highestSeed.players[0].user.id)
            # Low seed picks realm
            elif match.currentRealm is None:
                lowestSeed = min(match.teams, key=lambda t: t.seed)
                
                state.clear()
                state['name'] = 'chooseMap'
                state['action'] = 'pick'
                state['turn'] = str(lowestSeed.players[0].user.id)
            # Advance to next state
            else:
                state.clear()
                state['name'] = 'createRoom'
                
# List of rulesets
rulesets = {
    'basic': BasicRules(),
    'esl': ESLRules()
}
