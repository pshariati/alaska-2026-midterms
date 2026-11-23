"""Regression cases for Rachel's tokens, independent of prior CVR files."""
import unittest
from ranking_rules import interpret_tokens
H='Heikes, Gerald L.';P='Peltola, Mary';J='Sullivan, Daniel J. Jr.';D='Sullivan, Dan S.';W='Write-in';S='skipped';O='overvote'
class Rules(unittest.TestCase):
    def test_prefixes(self):
        cases=[([S,S,S,S,S],([], 'blank',None)),([P,S,S,S,S],([525],'end_of_ranks',None)),([P,S,D,S,S],([525,527],'end_of_ranks',None)),([P,S,S,D,S],([525],'two_consecutive_skips',3)),([S,S,D,S,S],([],'two_consecutive_skips',2)),([S,D,S,S,S],([527],'end_of_ranks',None)),([P,P,D,S,S],([525,527],'end_of_ranks',None)),([P,O,D,S,S],([525],'overvote',2)),([O,D,S,S,S],([],'overvote',1)),([P,S,W,S,D],([525,373,527],'end_of_ranks',None)),([P,S,S,W,D],([525],'two_consecutive_skips',3))]
        for ranks,result in cases:
            with self.subTest(ranks=ranks):self.assertEqual(interpret_tokens(ranks),result)
    def test_writein_occupancy(self):
        self.assertEqual([x for x in interpret_tokens([P,S,W,S,D])[0] if x!=373],[525,527])
    def test_unknown_fails(self):
        with self.assertRaises(ValueError):interpret_tokens(['Unknown candidate',S,S,S,S])
if __name__=='__main__':unittest.main(verbosity=2)
