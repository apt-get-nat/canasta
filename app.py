from kivy.app import App
from kivy.lang import Builder
from kivy.properties import *

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.togglebutton import ToggleButton

Builder.load_file('cards.kv')
class GCard(ToggleButton):
    cardfile = StringProperty()
    def __init__(self, suit, rank):
        super(GCard, self).__init__()
        if rank == 0:
            fname = 'back'
        elif rank == 1:
            fname = 'joker'
        else:
            fname = f"{suit}-{['2','3','4','5','6','7','8','9','10','j','q','k','a'][rank-2]}"
        self.cardfile = f"cards/{fname}.png"
        

class MainApp(App):
    def build(self):
        root = GridLayout(rows=2,cols=1)
        ghand = BoxLayout(orientation='horizontal', spacing=10)
        gtable = BoxLayout(orientation='horizontal')

        gtable.add_widget(GCard("clubs",3))
        gtable.add_widget(GCard("",0))
        
        ghand.add_widget(GCard("spades",14))
        ghand.add_widget(GCard("",1))
        ghand.add_widget(GCard("hearts",3))
        
        root.add_widget(gtable)
        root.add_widget(ghand)
        return root

MainApp().run()