import random

# for terminal display
LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'

CARD_POINTS = {1:50,
               2:20,
               3:100,
               4:5,5:5,6:5,7:5,
               8:10,9:10,10:10,11:10,12:10,13:10,
               14:20
}
MELD_POINTS = { **{('clean',3):1000,
                   ('clean',5):5000,
                   ('clean',7):2000,
                   ('wild','wild'):3000,
                   ('run','hearts'):2500,
                   ('run','clubs'):2500,
                   ('run','spades'):2500,
                   ('run','diamonds'):2500},
                **{('dirty',r):300 for r in range(4,15)},
                **{('clean',r):500 for r in [4,6,8,9,10,11,12,13,14]}
}

class Card:
    def __init__(self, rank, suit):
        """
        jokers are rank 1, aces rank 14
        suit is a string; for jokers it's empty'
        """
        assert suit in ["hearts","diamonds","clubs","spades",""]
        self.rank = rank
        self.suit = suit
        self.points = CARD_POINTS[rank]
    def __str__(self):
        if self.rank == 1:
            s = "W"
        elif self.rank == 11:
            s = "J"
        elif self.rank == 12:
            s = "Q"
        elif self.rank == 13:
            s = "K"
        elif self.rank == 14:
            s = "A"
        else:
            s = str(self.rank)
        if self.suit == "clubs":
            s = "♧" + s
        elif self.suit == "diamonds":
            s = "♢" + s
        elif self.suit == "hearts":
            s = "♡" + s
        elif self.suit == "spades":
            s = "♤" + s
        else: # joker
            s = "_" + s
        return s
    def iswild(self):
        if self.rank < 3:
            return True
        else:
            return False
    def __eq__(self, card):
        return self.rank == card.rank
    def __lt__(self, card):
        return self.rank < card.rank
    def __le__(self, card):
        return self.rank <= card.rank
class Deck:
    def __init__(self, decks):
        self.stack = [Card(r, "clubs") for r in range(2,15)] + [Card(r, "hearts") for r in range(2,15)] + [Card(r, "diamonds") for r in range(2,15)] + [Card(r, "spades") for r in range(2,15)] + [Card(1,"")]*2
        self.stack = self.stack*decks
        self.shuffle()
        self.discard_pile = self.deal(1)
    def __str__(self):
        return ",".join([str(c) for c in self.stack]) + \
             "|"+",".join([str(c) for c in self.discard_pile])
    def shuffle(self):
        random.shuffle(self.stack)
        return
    def deal(self, count):
        cards = []
        for j in range(count):
            cards.append(self.stack.pop())
        return cards
        
class Player:
    def __init__(self, deck, name="Player"):
        self.hand = deck.deal(15)
        self.butt = deck.deal(13)
        self.foot = deck.deal(11)
        self.name = name
        self.melds = []
        self.locked_melds = []
        return
    def draw(self, deck, cards = None):
        if cards is None:
            cards = deck.deal(2)
        if max([0]+[len(m.cards) for m in self.melds+self.locked_melds])>6:
            cards = cards + self.butt
            self.butt = []
        if len(self.hand) == 0:
            cards = cards + self.foot
            self.foot = []
        for j in range(len(cards)):
            if cards[j].rank == 3 and cards[j].suit in ['hearts','diamonds']:
                found = False
                for m in range(len(self.melds)):
                    if self.melds[m].type == ('clean',3):
                        self.melds[m].add(cards.pop(j))
                        found = True
                        if len(self.melds[m].cards) > 6:
                            self.locked_melds.append(self.melds.pop(m))
                        break
                if not found:
                    self.melds.append(Meld([cards.pop(j)]))
                self.draw(deck)
        for c in cards:
            self.hand.append(c)
        return
    def discard(self, card_idx, deck):
        deck.discard_pile.append(self.hand.pop(card_idx))
        return
    def pickup(self, idxs, deck, meld_idx = None):
        assert self.can_play([self.hand[j] for j in idxs]+[deck.discard_pile[-1]], meld_idx = meld_idx)
        self.play(idxs, meld_idx = meld_idx, discard_card = deck.discard_pile.pop())
        
        self.draw(deck, cards = deck.discard_pile)
        deck.discard_pile = []
        return
    def can_play(self, cards, meld_idx = None):
        cards.sort()
        if sum([c.rank == 3 and c.suit in ['hearts','diamonds'] for c in cards]) == len(cards):
            if meld_idx is None:
                if 3 not in [m.type[1] for m in self.melds] and len(cards) < 8:
                    return True
            else:
                if self.melds[meld_idx].type == ('clean',3) and len(self.melds[meld_idx].cards) + len(cards) < 8:
                    return True
                else:
                    return False
        if sum([c.rank == 3 for c in cards]) > 0:
            return False
        if meld_idx is None:
            if sum([c.rank in [5,7] for c in cards]) > 0 and sum([c.iswild() for c in cards]) > 0:
                # 5 and 7 can't be dirty'
                return False
            if len(cards) < 3 or len(cards) > 7:
                # new books must be 3-7 cards
                return False
            if ( cards.count(cards[-1]) + sum([c.iswild() for c in cards]) == len(cards)
                 and cards.count(cards[-1]) > len(cards)/2
               ) or sum([c.iswild() for c in cards]) == len(cards):
                # book is valid clean, dirty or wilds
                if cards[-1].rank in [m.type[1] for m in self.melds] \
                    or (cards[-1].iswild() and 'wilds' in [m.type[1] for m in self.melds]):
                    # can't have multiple matching books going
                    return False
                return True
            if ( [c.rank+1 for c in cards[:-1]] == [c.rank for c in cards[1:]]
                 and min([c.rank for c in cards])>3
                 and [c.suit for c in cards].count(cards[0].suit) == len(cards)
               ):
                # is valid run
                if sum([m.type[0] == 'run' for m in self.melds + self.locked_melds]) < 2:
                    # can only attempt two runs
                    return True
            return False
        else:
            meld = self.melds[meld_idx]
            if len(meld.cards) + len(cards) > 7:
                return False
            match meld.type[0]:
                case 'clean':
                    if meld.type[1] in [5,7] and sum([c.iswild() for c in cards]) > 0:
                        return False
                    if sum([c.rank != meld.type[1] for c in cards if not c.iswild()]) == 0 and \
                       sum([c.iswild() for c in cards]) < (len(cards)+len(meld.cards))/2:
                        return True
                    else:
                        return False
                case 'dirty':
                    if sum([c.rank != meld.type[1] for c in cards if not c.iswild()]) == 0 and \
                       sum([c.iswild() for c in cards]) + sum([c.iswild() for c in meld.cards]) < (len(cards)+len(meld.cards))/2:
                        return True
                    else:
                        return False
                case 'wilds':
                    if sum([not c.iswild() for c in cards]) == 0:
                        return True
                    else:
                        return False
                case 'run':
                    ranks = [c.rank for c in cards] + [c.rank for c in meld.cards]
                    ranks.sort()
                    if [c.suit for c in cards].count(meld.type[1]) < len(cards):
                        return False
                    if ranks[0] < 3:
                        return False
                    if [r+1 for r in ranks[:-1]] == ranks[1:]:
                        return True
                    else:
                        return False
            assert False, f'unrecognized meld type {meld.type[0]}'
    def play(self,idxs, meld_idx = None, discard_card = None):
        idxs.sort(reverse=True)
        assert idxs[0] < len(self.hand), 'index out of bounds'
        if meld_idx is not None:
            assert meld_idx < len(self.melds), 'index out of bounds'
            
        cards = [self.hand[j] for j in idxs]
        if discard_card is not None:
            cards.append(discard_card)
        
        assert self.can_play(cards, meld_idx=meld_idx), 'cannot play'
        
        [self.hand.pop(j) for j in idxs]
        if meld_idx is None:
            self.melds.append(Meld(cards))
            meld_idx = -1
        else:
            cards.sort(reverse=True)
            for c in cards:
                self.melds[meld_idx].add(c)
        if len(self.melds[meld_idx].cards)>6:
            if self.melds[meld_idx].type[1] in ['hearts','diamonds','spades','clubs',3,5,7] \
                or self.melds[meld_idx].type[0] not in [m.type[0] for m in self.locked_melds]:
                self.locked_melds.append(self.melds.pop(meld_idx))
        return True
        
class Meld:
    def __init__(self, cards):
        assert len(cards) > 2 or sum([c.rank == 3 for c in cards]) == len(cards)
        cards.sort()
        wilds = sum([c.iswild() for c in cards])
        if wilds == 0:
            if cards.count(cards[0]) == len(cards):
                self.type = ('clean',cards[-1].rank)
            else:
                self.type = ('run',cards[-1].suit)
        elif wilds == len(cards):
            self.type = ("wilds","wilds")
        else:
            self.type = ("dirty",cards[-1].rank)
        self.cards = cards
    def __str__(self):
        return f'[{self.cards[0]}-{len(self.cards)}-{self.cards[-1]}|{self.type}]'
    def isdone(self):
        return len(self.cards) > 6
    def wilds(self):
        return sum([c.iswild() for c in self.cards])
    def add(self, card):
        print(str(self), str(card))
        if self.type[0] == 'wilds':
            assert card.iswild()
        elif self.type[0] == 'dirty':
            assert self.wilds()+card.iswild() < (len(self.cards)+1)/2
            assert self.type[1] == card.rank or card.iswild()
        elif self.type[0] == 'clean':
            if card.iswild():
                self.type = ('dirty',self.type[1])
            else:
                assert self.type[1] == card.rank
        
        self.cards.append(card)
        if self.type[0] == 'run':
            self.cards.sort()
        
    def score(self):
        points = 0
        if len(self.cards) > 6:
            points = points + MELD_POINTS[self.type]
        if not (type[1] == 3 and len(self.cards)>6):
            for c in self.cards:
                points = points + c.points
        return points
class Game:
    def __init__(self, players=2):
        self.players = []
        if players == 2:
            self.deck = Deck(6)
        elif players == 4:
            self.deck = Deck(8)
        else:
            assert False, "Unsupported player count"
        for j in range(players):
            self.players.append(Player(self.deck,name=f'Player {j+1}'))
        self.turn = 0
    def score(self):
        scores = [0]*len(self.players)
        for j in range(len(self.players)):
            for m in self.players.locked_melds:
                scores[j] = scores[j] + m.score()
            for m in self.players.melds:
                scores[j] = scores[j] + m.score()
            stuck = self.players[j].hand + self.players[j].butt + self.players[j].foot
            for c in stuck:
                scores[j] = scores[j]-CARD_POINTS[c.rank]
                if c.rank == 3 and c.suit in ['hearts','diamonds']:
                    scores[j] = scores[j] - 200 # additional penalty
            return scores
                
    def update_display(self):
        self.players[self.turn].hand.sort()
        for j in range(20):
            print(LINE_UP, end=LINE_CLEAR)
        if len(self.deck.discard_pile)>0:
            print(f'[{self.deck.discard_pile[-1]}][ππ]')
        else:
            print('[  ][ππ]')
#        print(str(self.deck))
        for p in self.players:
            print(f"{p.name}'s melds:")
            print([str(m) for m in p.locked_melds])
            print([str(m) for m in p.melds])
        print(f"{self.players[self.turn].name}'s hand:")
        print([str(c) for c in self.players[self.turn].hand])
    def update(self):
        message = ""
        while True:
            self.update_display()
            print(message)
            message = ""
            d = input('draw? >')
            if len(d)>0:
                try:
                    idxs = [int(j)-1 for j in d.split(' ')]
                    assert len(idxs) > 2
                except:
                    message ="invalid input!"
                    continue
                midx = idxs.pop()
                if midx == -1:
                    midx = None
                try:
                    self.players[self.turn].pickup(idxs, self.deck, meld_idx=midx)
                    break
                except AssertionError as e:
                    message = str(e)
                    continue
            else:
                self.players[self.turn].draw(self.deck)
                break
        while True:
            self.update_display()
            print(message)
            message = ""
            p = input('play c1 c2 ... cn meld, 0 for new meld >')
            if len(p) == 0:
                break
            try:
                idxs = [int(j)-1 for j in p.split(' ')]
                assert len(idxs) > 1
            except:
                message ="invalid input!"
                continue
            if idxs[-1] == -1:
                midx = None
            else:
                midx = idxs[-1]
            idxs = idxs[:-1]
            try:
                self.players[self.turn].play(idxs, meld_idx = midx)
            except AssertionError as e:
                message = str(e)
                continue
        self.update_display()
        d = input('discard c1 >')
        self.players[self.turn].discard(int(d)-1, self.deck)
        return

def main():
    g = Game()
    while True:
        g.update()
        g.turn = (g.turn + 1) % len(g.players)
        
        for j in range(20):
            print(LINE_UP, end=LINE_CLEAR)
        pause = input("Next player")

if __name__ == '__main__':
    main()