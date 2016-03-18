import util

class BanRule:
    """
    Class that handles ban and pick orders for matches.
    """
    def __init__(self):
        pass
        
    def advanceState(self, match):
        """
        Handles all of the logic of what the next state should be.
        
        Directly modifies match.state.
        """
        raise NotImplementedError('No generic getNextState')
    
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

class BasicRules:
    """
    A basic implementation of rules.
    """
    # override
    def advanceState(self, match):
        state = match.state
        # Entry point into the cyclic states, straight to pickLegends
        if state['name'] == 'waitingForPlayers':
            state.clear()
            state['name'] = 'pickLegends'
        
        if state['name'] == 'pickLegends':
            self._getNextLegendStep(match)
        
        # Note that this is intentionally not elif
        if state['name'] == 'chooseMap':
            self._getNextMapStep(match)
            
    # override
    def _getNextLegendStep(self, match):
        """
        Basic picking order. Higher seed
        """
        match.state.clear()
        
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
            match.state['name'] = 'chooseMap'
            return
        
        match.state['canPick'] = userIds
    
    def _getNextMapStep(self, match):
        """
        Basic pick ban order.
        """
        currentBans = match.getRealmBans()
        state = match.state
        # Ban up until 2 maps left
        if len(currentBans) < (len(util.realmData) - 2):
            state.clear()
            state['name'] = 'chooseMap'
            
            # Player 0 == captain
            state['turn'] = match.teams[len(currentBans)%2]\
                                .players[0].user.id
            state['action'] = 'ban'
        elif match.currentRealm is None:
            state.clear()
            state['name'] = 'chooseMap'
            
            # Player 0 == captain
            state['turn'] = match.teams[len(currentBans)%2]\
                                .players[0].user.id
            state['action'] = 'pick'
        else:
            state.clear()
            state['name'] = 'createRoom'

# List of rulesets
rulesets = {
    'basic': BasicRules()
}