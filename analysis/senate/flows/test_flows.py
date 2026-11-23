from analysis.senate.flows.build_flows import prefix
p='Peltola, Mary';d='Sullivan, Dan S.';w='Write-in';s='skipped';o='overvote'
assert prefix([s]*5)==[]
assert prefix([p,s,s,s,s])==['peltola']
assert prefix([s,p,s,s,s])==['peltola']
assert prefix([p,s,s,d,s])==['peltola']
assert prefix([p,s,w,s,d])==['peltola','writein','dan_sullivan']
assert prefix([p,o,d,s,s])==['peltola']
assert prefix([o,p,d,s,s])==[]
assert prefix([p,p,d,s,s])==['peltola','dan_sullivan']
print('Eight parser regression cases passed.')
