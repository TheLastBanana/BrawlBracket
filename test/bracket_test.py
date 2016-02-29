import json
from brawlbracket.bracket.tournament import SingleElimTournament

def tourneyFromFile(filename):
    """
    Load a tourney from a dump file.
    """
    with open(filename, 'r') as inFile:
        tourneyData = json.loads(inFile.read())

    matchDataById = tourneyData['matches']
    participantDataById = tourneyData['participants']
        
    matches = {}

    # Create a tourney to fit the participants
    # Pass '' as shortName, it doesn't matter here
    tourney = SingleElimTournament('', len(participantDataById))

    # Sort teams so we can get them by seed
    teams = list(tourney.teams)
    teams.sort(key=lambda team: team.seed)

    # Create a match in the tournament for each of the Challonge matches
    for id in matchDataById:
        matches[id] = tourney.createMatch()
        
    # Now that the matches exist, connect them to each other
    for id in matchDataById:
        matchData = matchDataById[id]
        match = matches[id]
        
        match.prereqMatches = [matches[str(prereqId)] if prereqId else None for prereqId in matchData['prereqs']]
        match.teams = [teams[seed - 1] if seed else None for seed in matchData['teams']]

    # Find the root node, which will have no next match
    for match in tourney.matches:
        if match.nextMatch is None:
            tourney.root = match
            break
            
    tourney.finalize()

    return tourney
    
def matchTreesEqual(rootA, rootB):
    """
    Compare two match trees. We don't use the __eq__ function on the matches, because that doesn't compare the data
    that we're interested in. Instead, we want to check that the trees are laid out the same way.
    """
    
    # If one doesn't exist, both shouldn't exist
    if rootA is None:
        return rootB is None
            
    # This match is equal if its prereqs are equal on each side
    return matchTreesEqual(rootA.prereqMatches[0], rootB.prereqMatches[0]) and \
           matchTreesEqual(rootA.prereqMatches[1], rootB.prereqMatches[1])
           
        
def pytest_generate_tests(metafunc):
    """
    Parameterize the tests
    """
    if 'tourneySize' in metafunc.funcargnames:
        for i in range(2, 65):
            metafunc.addcall(funcargs=dict(tourneySize=i))
            
def test_singleElimTraditional(tourneySize):
    """
    Test single elimination tournament generation against premade data.
    """
    premade = tourneyFromFile('test/data/single-elim-traditional/{}.tourney'.format(tourneySize))
    
    # Pass '' as shortName, it doesn't matter here
    generated = SingleElimTournament('', tourneySize)
    generated.generateMatches()
    
    print('Testing single elimination tournament size {}'.format(tourneySize))
    print('Expecting:')
    print(premade)
    print('Got:')
    print(generated)
    
    assert matchTreesEqual(premade.root, generated.root)