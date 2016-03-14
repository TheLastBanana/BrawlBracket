

class BanRule:
    """
    Class that handles ban and pick orders for matches.
    """
    def __init__(self):
        pass
    
    def getNextLegendStep(self, match):
        """
        Intended to determine the next step in the legend picking process.
        This could be the next person to pick or ban.
        
        Returns a dictionary info:
            canPick: list of playerIds who can pick (list of str)
        """
        raise NotImplementedError('No generic getNextLegendStep')

class BasicRules:
    """
    A basic implementation of rules.
    """
    
    #override
    def getNextLegendStep(self, match):
        """
        Basic picking order. Higher seed
        """
        teams = list(match.teams)
        teams.sort(key = lambda t: t.seed, reverse = True)
        
        userIds = None
        if any(p.currentLegend is None for p in teams[0].players):
            userIds = [str(p.user.id) for p in teams[0].players
                            if p.currentLegend is None]
        else:
            userIds = [str(p.user.id) for p in teams[1].players
                            if p.currentLegend is None]
        
        data = {}
        data['canPick'] = userIds
        
        return data

# List of rulesets
rulesets = {
    'basic': BasicRules()
}