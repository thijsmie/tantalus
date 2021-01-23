from asciimatics.widgets import Frame, Layout, MultiColumnListBox, Label, Widget, Text, Divider, PopupMenu
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.event import KeyboardEvent
from asciimatics.effects import Print
from asciimatics.renderers import ColourImageFile
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication

from collections import defaultdict
import os
import sys

from .application import Application, TextAction, TextActionType
from .config import get_config


class UiHolder:
    def __init__(self):
        self.frames = []

    def append(self, frame):
        self.frames.append(frame)

    def raise_events(self, events):
        saved_exc = None
        for event in events:
            for frame in self.frames:
                try:
                    frame.event(event)
                except Exception as e:
                    saved_exc = e
        if saved_exc:
            raise saved_exc


class Instructions(Frame):
    def __init__(self, screen, holder, app: Application):
        self.holder = holder
        self.holder.append(self)
        self.app = app

        super().__init__(screen, 
                         20, 
                         int(screen.width / 2) - 2, 
                         has_border=False, 
                         name="Instructions",
                         x=int(screen.width / 2) + 1, 
                         y=18
        )

        layout = Layout([1], fill_frame=True)

        self.add_layout(layout)
        layout.add_widget(Label("Tantalus POS Endpoint"))
        layout.add_widget(Divider())
        layout.add_widget(Label(app.instructions))
        layout.add_widget(Label(""))
        self.feedback = Label("")
        layout.add_widget(self.feedback)

        self.palette = defaultdict(lambda: (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK))
        self.fix()

    def event(self, event):
        if event.action_type == TextActionType.Feedback:
            self.feedback.text = event.content
        else:
            self.feedback.text = ""


class Basket(Frame):
    def __init__(self, screen, holder, app: Application):
        self.holder = holder
        self.holder.append(self)
        self.app = app

        super().__init__(screen, 
                         screen.height - 4, 
                         int(screen.width / 2) - 2, 
                         has_border=True, 
                         name="Basket", 
                         x=1, 
                         y=1,
                         title="Basket")

        layout = Layout([1], fill_frame=True)

        self._basket = MultiColumnListBox(
            Widget.FILL_FRAME,
            ['<60%', '>20%', '>20%'],
            [],
            titles=["Item", "Amount", "Price"],
            name="basket"
        )
        self._basket.custom_colour = "basket"
        self._basket.disabled = True

        self.add_layout(layout)
        layout.add_widget(self._basket)

        # Add my own colour palette
        self.palette = defaultdict(
            lambda: (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE))
        for key in ["selected_focus_field", "label"]:
            self.palette[key] = (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_WHITE)
        self.palette["basket"] = (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE)
        self.fix()
        
    def event(self, event: TextAction):
        if event.action_type == TextActionType.BasketRefresh:
            self._basket.options = self.app.basket.ui_format()


class Scanner(Frame):
    def __init__(self, screen, holder, app: Application):
        self.holder = holder
        self.holder.append(self)
        self.app = app

        super().__init__(screen, 
                         1, 
                         int(screen.width / 2) - 2, 
                         has_border=False, 
                         name="Scanner", 
                         x=1,
                         y=screen.height - 1
        )

        layout = Layout([1], fill_frame=True)

        self._input = Text("Scan: ")

        self.add_layout(layout)
        layout.add_widget(self._input)

        # Add my own colour palette
        self.palette = defaultdict(
            lambda: (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK))
        for key in ["selected_focus_field", "label"]:
            self.palette[key] = (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK)
        self.palette["basket"] = (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK)

        self.fix()
        self._input.focus()

    def process_event(self, event):
        if (event is not None and isinstance(event, KeyboardEvent)):
            if event.key_code == 10:
                self.holder.raise_events(self.app.text_action(self._input.value))
                self._input.value = ""
                return
        super().process_event(event)

    def event(self, event):
        pass


class SearchHandler:
    def __init__(self, scene, screen, holder, app: Application):
        self.scene = scene
        self.screen = screen
        self.holder = holder
        self.holder.append(self)
        self.app = app

    def event(self, event: TextAction):
        if event.actiontype == TextActionType.SearchResults:
            options = [
                (product.name, self.event_raiser(product))
                for product in event.content
            ]
            self.scene.add_effect(PopupMenu(self.screen, options, 1, 1))

    def event_raiser(self, product):
        def raiser():
            self.holder.raise_events(self.app.search_submit(product))
        return raiser


def draw_logo(screen):
    return Print(screen, 
        ColourImageFile(
            screen, 
            os.path.abspath(os.path.dirname(__file__)) + "/drop.png", 
            16, 
            uni=screen.unicode_aware
        ),
        x=screen.width - 32, 
        y=0
    )

    
def main_interface(screen, app):
    holder = UiHolder()

    scene = Scene([
        draw_logo(screen),
        Basket(screen, holder, app),
        Instructions(screen, holder, app),
        Scanner(screen, holder, app)
    ], -1, name="main")

    SearchHandler(scene, screen, holder, app)

    return scene


def interface(screen, scene, app):
    screen.play([main_interface(screen, app)], stop_on_resize=True, start_scene=scene, allow_int=True)


def run_interface(app):
    last_scene = None
    while True:
        try:
            Screen.wrapper(interface, catch_interrupt=False, arguments=[last_scene, app])
            sys.exit(0)
        except ResizeScreenError as e:
            last_scene = e.scene
        except KeyboardInterrupt:
            sys.exit(0)



app = Application(get_config())
app.instructions="Blah"
run_interface(app)