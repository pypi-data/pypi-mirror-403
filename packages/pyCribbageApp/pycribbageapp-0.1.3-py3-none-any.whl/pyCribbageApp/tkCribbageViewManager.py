"""
This module defines the tkCribbageViewManager class, which is a concrete implementation of tkViewManager for a cribbage application.
Acts as Observer, and handles the interactions between the cribbage app's board, crib, starter card, human player's hand, game play pile,
and scoring information widgets, which are also defined in this module.

Note that the CribbageApp class Has three view managers:
1. tkUserQueryViewManager -- handles the user query widgets and interactions
2. tkSimulatorViewManager -- handles the widgets and interactions for showing all simulator output log records as text messages
3. tkCribbageViewManager -- handles cribbage-specific widgets and interactions, for showing structured cribbage game output

Exported Classes:
    tkCribbageViewManager -- Concrete implementation of tkViewManager for a cribbage simulator application

Exported Exceptions:
    None    
 
Exported Functions:
    None
"""


# Standard imports
from logging import LogRecord
import tkinter as tk
from tkinter import ttk
from functools import partial

# Local imports
from CribbageSim.CribbageGameOutputEvents import CribbageGameOutputEvents
from tkAppFramework.tkViewManager import tkViewManager
from tkAppFramework.ObserverPatternBase import Subject


class tkCribbageViewManager(tkViewManager):
    """
    This class follows the mediator design pattern. It handles interactions between widgets that are specific to cribbage.
    """
    # TODO: Reserach if the player names need to be passed in and become attributes, since the CribbageGameOutputEvents appear to carry the names as needed.
    # But, YES!, see handle_start_deal_event().
    def __init__(self, parent, name1='', name2='') -> None:
        """
        :parameter parent: The parent widget of this widget, The tkinter App
        :parameter name1: The name of player 1, string
        :parameter name2: The name of player 1, string
        """
        self._player1_name = name1
        self._player2_name = name2
        
        super().__init__(parent)


        # TODO: In a later refactoring, could have a "registration" function to register handlers.
        # Create a dictionary of callables to handle each specific type of game output event
        self._game_event_handlers = {}
        self._game_event_handlers[CribbageGameOutputEvents.START_GAME] = self.handle_start_game_event
        self._game_event_handlers[CribbageGameOutputEvents.START_DEAL] = self.handle_start_deal_event
        self._game_event_handlers[CribbageGameOutputEvents.UPDATE_PLAYER1_HAND] = self.handle_update_player1_hand_event
        self._game_event_handlers[CribbageGameOutputEvents.UPDATE_PLAYER2_HAND] = self.handle_update_player2_hand_event
        self._game_event_handlers[CribbageGameOutputEvents.UPDATE_PLAYER1_PILE] = self.handle_update_player1_pile_event
        self._game_event_handlers[CribbageGameOutputEvents.UPDATE_PLAYER2_PILE] = self.handle_update_player2_pile_event
        self._game_event_handlers[CribbageGameOutputEvents.UPDATE_STARTER] = self.handle_update_starter_event
        self._game_event_handlers[CribbageGameOutputEvents.UPDATE_CRIB] = self.handle_update_crib_event
        self._game_event_handlers[CribbageGameOutputEvents.UPDATE_PILE_COMBINED] = self.handle_update_pile_combined_event
        self._game_event_handlers[CribbageGameOutputEvents.UPDATE_SCORE_PLAYER1] = self.handle_update_score_player1_event
        self._game_event_handlers[CribbageGameOutputEvents.UPDATE_SCORE_PLAYER2] = self.handle_update_score_player2_event
        self._game_event_handlers[CribbageGameOutputEvents.END_GAME] = self.handle_end_game_event
  
        self._CreateWidgets()

    def reset_widgets_for_new_deal(self):
        """
        Utility function called to put child widgets in appropriate state ahead of a new deal.
        :return None:
        """
        self._crib_widget.reset_widgets_for_new_deal()
        self._starter_widget.reset_widgets_for_new_deal()
        self._play_pile_widget.reset_widgets_for_new_deal()
        self._player_hand_widget.reset_widgets_for_new_deal()
        self._scores_widget.reset_widgets_for_new_deal()
        
        return None

    def handle_model_update(self):
        """
        Handler function called when the model notifies the tkViewManager of a change in state. Must be implemented
        by subclasses.
        
        IN this implementation, the method is the switchboard for output events from CribbageGame which the CribbageGame expects the app to visualize and the app expects
        the tkCribbageViewManager to visualize.
        :return None:
        """
        # Retrieve a LogRecord from the simulator event queue
        info = self.getModel().log_record
        if info is not None:
            # Make sure we are retrieving what we think we are retrieving, that is, a LogRecord object
            assert(isinstance(info, LogRecord))
            
            # If possible, dispatch to the appropriate handler
            if 'event_type' in info.__dict__:
                # At this point we can assume that the LogRecord has been populated with the extra CribbageGameLogInfo attributes
                # Call the right handler for the event type
                self._game_event_handlers[info.event_type](info)

        return None

    def handle_start_game_event(self, info):
        """
        Called to handle START_GAME game output event.
        :parameter info: LogRecord object containing CribbageGameLogInfo attribute
        :return: None
        """
        assert(info.event_type == CribbageGameOutputEvents.START_GAME)

        self._player1_name = info.name_player1
        self._player2_name = info.name_player2

        self._board_widget._player1_track['text']=f"{info.name_player1}"
        self._board_widget._player2_track['text']=f"{info.name_player2}"

        # Set the name of player 1 in the label frame of the CribbagePlayerHandWidget
        self._player_hand_widget['text']=f"{self._player1_name} Hand"
        
        self.reset_widgets_for_new_deal()

        self._board_widget.set_pegs_player1()
        self._board_widget.set_pegs_player2()
        
        return None

    def handle_end_game_event(self, info):
        """
        Called to handle END_GAME game output event
        :parameter info: LogRecord object containing CribbageGameLogInfo attribute
        :return: None
        """
        assert(info.event_type == CribbageGameOutputEvents.END_GAME)
        # Ask the app to end the game
        self.master.onFileExit()
        return None

    def handle_start_deal_event(self, info):
        """
        Called to handle START_DEAL game output event.
        :parameter info: LogRecord object containing CribbageGameLogInfo attribute
        :return: None
        """
        assert(info.event_type == CribbageGameOutputEvents.START_DEAL)
        if info.name_dealer == self._player1_name:
            self._board_widget._player1_track['text']=f"{self._player1_name} - Dealer"
            self._board_widget._player2_track['text']=f"{self._player2_name}"
        elif info.name_dealer == self._player2_name:
            self._board_widget._player2_track['text']=f"{self._player2_name} - Dealer"
            self._board_widget._player1_track['text']=f"{self._player1_name}"
            
        self.reset_widgets_for_new_deal()
        
        return None

    def handle_update_player1_hand_event(self, info):
        """
        Called to handle UPDATE_PLAYER1_HAND game output event.
        :parameter info: LogRecord object containing CribbageGameLogInfo attribute
        :return: None
        """
        assert(info.event_type == CribbageGameOutputEvents.UPDATE_PLAYER1_HAND)
        self._player_hand_widget.reset_widgets_for_new_deal()
        # Get the list of crib card strings from info
        card_list = info.hand_player1.split()
        for i in range(len(card_list)):
            self._player_hand_widget._lbls_cards[i].set(card_list[i])
        return None

    def handle_update_player2_hand_event(self, info):
        """
        Called to handle UPDATE_PLAYER2_HAND game output event.
        :parameter info: LogRecord object containing CribbageGameLogInfo attribute
        :return: None
        """
        # Should only arrive here if the logging QueueHandler is set at DEBUG level. We have no widget for displaying the hand of player 2
        # at this time, so do nothing, as the dispatcher self.CribbageGameOutputEventHandler() will have sent the debug message to the
        # info widget.
        return None

    def handle_update_player1_pile_event(self, info):
        """
        Called to handle UPDATE_PLAYER1_PILE game output event.
        :parameter info: LogRecord object containing CribbageGameLogInfo attribute
        :return: None
        """
        # We have no widget for displaying the player 1 pile at this time, so do nothing, the dispatcher
        # self.CribbageGameOutputEventHandler() will have sent the debug message to the info widget.
        return None

    def handle_update_player2_pile_event(self, info):
        """
        Called to handle UPDATE_PLAYER2_PILE game output event.
        :parameter info: LogRecord object containing CribbageGameLogInfo attribute
        :return: None
        """
        # We have no widget for displaying the player 1 pile at this time, so do nothing, the dispatcher
        # self.CribbageGameOutputEventHandler() will have sent the debug message to the info widget.
        return None

    def handle_update_starter_event(self, info):
        """
        Called to handle UPDATE_STARTER game output event.
        :parameter info: LogRecord object containing CribbageGameLogInfo attribute
        :return: None
        """
        assert(info.event_type == CribbageGameOutputEvents.UPDATE_STARTER)
        self._starter_widget._lbl_starter.set(info.starter)
        return None

    def handle_update_crib_event(self, info):
        """
        Called to handle UPDATE_CRIB game output event.
        :parameter info: LogRecord object containing CribbageGameLogInfo attribute
        :return: None
        """
        assert(info.event_type == CribbageGameOutputEvents.UPDATE_CRIB)
        self._crib_widget.reset_widgets_for_new_deal()
        # Get the list of crib card strings from info
        card_list = info.crib.split()
        for i in range(len(card_list)):
            self._crib_widget._lbls_cards[i].set(card_list[i])
        return None

    def handle_update_pile_combined_event(self, info):
        """
        Called to handle UPDATE_PILE_COMBINED game output event.
        :parameter info: LogRecord object containing CribbageGameLogInfo attribute
        :return: None
        """
        assert(info.event_type == CribbageGameOutputEvents.UPDATE_PILE_COMBINED)
        self._play_pile_widget.reset_widgets_for_new_deal()
        # Get the list of pile card strings from info
        card_list = info.pile_combined.split()
        # Label the card buttons according to the card list
        for i in range(len(card_list)):
            self._play_pile_widget._lbls_cards[i].set(card_list[i])
        # Set the GO round count in the frame label
        self._play_pile_widget.set_go_round_count(info.go_round_count)
        return None

    def handle_update_score_player1_event(self, info):
        """
        Called to handle UPDATE_SCORE_PLAYER1 game output event.
        :parameter info: LogRecord object containing CribbageGameLogInfo attribute
        :return: None
        """
        assert(info.event_type == CribbageGameOutputEvents.UPDATE_SCORE_PLAYER1)
        self._board_widget.set_pegs_player1(info.score_player1[0], info.score_player1[1])
        
        # Add scoring reason record to the CribbageScoresInfoWidget
        self._scores_widget.add_scoring_combo_info(self._player1_name, info.score_while, info.score_record)
        
        return None
    
    def handle_update_score_player2_event(self, info):
        """
        Called to handle UPDATE_SCORE_PLAYER2 game output event.
        :parameter info: LogRecord object containing CribbageGameLogInfo attribute
        :return: None
        """
        assert(info.event_type == CribbageGameOutputEvents.UPDATE_SCORE_PLAYER2)
        self._board_widget.set_pegs_player2(info.score_player2[0], info.score_player2[1])

        # Add scoring reason record to the CribbageScoresInfoWidget
        self._scores_widget.add_scoring_combo_info(self._player2_name, info.score_while, info.score_record)
        
        return None
    
    def handle_child_widget_updates(self):
        """
        Handler function called when any child widget object notifies the tkCribbageViewManager of a change in state.
        Currently does nothing.
        :return None:
        """
        # Do nothing
        # TODO: Determine if this should do something.
        return None

    def _CreateWidgets(self):
        """
        Utility function to be called by __init__ to set up the child widgets of the tkCribbageViewManager widget.
        :return None:
        """

        self._board_widget = CribbageBoardWidget(self, self._player1_name, self._player2_name)
        self.register_subject(self._board_widget, self.handle_child_widget_updates)
        self._board_widget.attach(self)
        self._board_widget.grid(column=0, row=0, rowspan=5, sticky='NWES') # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.rowconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx

        self._starter_widget = CribbageStarterCardWidget(self)
        self.register_subject(self._starter_widget, self.handle_child_widget_updates)
        self._starter_widget.attach(self)
        self._starter_widget.grid(column=1, row=0, sticky='NWES') # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(1, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.rowconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx

        self._crib_widget = CribbageCribWidget(self)
        self.register_subject(self._crib_widget, self.handle_child_widget_updates)
        self._crib_widget.attach(self)
        self._crib_widget.grid(column=2, row=0, sticky='NWES') # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(2, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.rowconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        
        self._player_hand_widget = CribbagePlayerHandWidget(self, self._player1_name)
        self.register_subject(self._player_hand_widget, self.handle_child_widget_updates)
        self._player_hand_widget.attach(self)
        self._player_hand_widget.grid(column=1, row=1, columnspan=2, sticky='NWES') # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(1, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.rowconfigure(1, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx

        self._play_pile_widget = CribbagePlayPileWidget(self)
        self.register_subject(self._play_pile_widget, self.handle_child_widget_updates)
        self._play_pile_widget.attach(self)
        self._play_pile_widget.grid(column=1, row=2, columnspan=2, sticky='NWES') # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(1, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.rowconfigure(2, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        
        self._scores_widget = CribbageScoresInfoWidget(self)
        self.register_subject(self._scores_widget, self.handle_child_widget_updates)
        self._scores_widget.attach(self)
        self._scores_widget.grid(column=1, row=3, columnspan=2, sticky='NWES') # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(1, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.rowconfigure(3, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx

        return None


class CribbagePlayerHandWidget(ttk.Labelframe, Subject):
    """
    Class represents a tkinter label frame, the widget contents of which will represent a player's hand visually in the application.
    """
    def __init__(self, parent, name1='') -> None:
        """
        :parameter parent: tkinter widget that is the parent of this widget
        :parameter name1: Name of player 1 , string
        """
        super().__init__(parent, text=f"{name1} Hand")
        Subject.__init__(self)
        
        # List of buttons representing cards in the hand
        self._btns_cards = []
        # List of StringVar control variables for the card labels
        self._lbls_cards = []
        
        # Note: partial is used in order to be able to pass along a button index to the command function, which otherwise takes no arguments
        # See: (https://stackoverflow.com/questions/6920302/how-to-pass-arguments-to-a-button-command-in-tkinter)
        self._btns_cards.append(tk.Button(self, command=partial(self.OnCardButtonClick, 0)))
        self._btns_cards[0].grid(column=0, row=0) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.rowconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self._btns_cards[0]['state']=tk.DISABLED
        self._lbls_cards.append(tk.StringVar())
        self._lbls_cards[0].set('--')
        self._btns_cards[0]['textvariable']=self._lbls_cards[0]

        self._btns_cards.append(tk.Button(self, command=partial(self.OnCardButtonClick, 1)))
        self._btns_cards[1].grid(column=1, row=0) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(1, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self._btns_cards[1]['state']=tk.DISABLED
        self._lbls_cards.append(tk.StringVar())
        self._lbls_cards[1].set('--')
        self._btns_cards[1]['textvariable']=self._lbls_cards[1]

        self._btns_cards.append(tk.Button(self, command=partial(self.OnCardButtonClick, 2)))
        self._btns_cards[2].grid(column=2, row=0) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(2, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self._btns_cards[2]['state']=tk.DISABLED
        self._lbls_cards.append(tk.StringVar())
        self._lbls_cards[2].set('--')
        self._btns_cards[2]['textvariable']=self._lbls_cards[2]

        self._btns_cards.append(tk.Button(self, command=partial(self.OnCardButtonClick, 3)))
        self._btns_cards[3].grid(column=3, row=0) # Grid-2 in Documentation\UI_WireFrame.pptx
        self._btns_cards[3]['state']=tk.DISABLED
        self.columnconfigure(3, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self._lbls_cards.append(tk.StringVar())
        self._lbls_cards[3].set('--')
        self._btns_cards[3]['textvariable']=self._lbls_cards[3]

        self._btns_cards.append(tk.Button(self, command=partial(self.OnCardButtonClick, 4)))
        self._btns_cards[4].grid(column=4, row=0) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(4, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self._btns_cards[4]['state']=tk.DISABLED
        self._lbls_cards.append(tk.StringVar())
        self._lbls_cards[4].set('--')
        self._btns_cards[4]['textvariable']=self._lbls_cards[4]

        self._btns_cards.append(tk.Button(self, command=partial(self.OnCardButtonClick, 5)))
        self._btns_cards[5].grid(column=5, row=0) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(5, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self._btns_cards[5]['state']=tk.DISABLED
        self._lbls_cards.append(tk.StringVar())
        self._lbls_cards[5].set('--')
        self._btns_cards[5]['textvariable']=self._lbls_cards[5]

        for b in self._btns_cards:
             b['height']=8
             b['width']=10
             b['relief']=tk.RIDGE

    def reset_widgets_for_new_deal(self):
        """
        Utility function called to put child widgets in appropriate state ahead of a new deal.
        :return None:
        """
        # Clear all current card lables in the crib widget
        for sv in self._lbls_cards: sv.set('--')
        return None

    def OnCardButtonClick(self, index):
        """
        Inform the mediator object which index button was pressed. Use Subject notify method? Currently does nothing.
        :parameter index: Index of button pressed, integer
        """
        pass

    def OnUndoButtonClick(self):
        """
        # Inform the mediator object. Use Subject notify method? Currently does nothing.
        """
        pass


class CribbageStarterCardWidget(ttk.Labelframe, Subject):
    """
    Class represents a tkinter label frame, the widget contents of which will represent the starter card visually in the application.
    """
    def __init__(self, parent) -> None:
        """
        :parameter parent: tkinter widget that is the parent of this widget
        """
        super().__init__(parent, text='Starter')
        Subject.__init__(self)
        
        self._btn_starter = tk.Button(self)
        self._btn_starter.grid(column=0, row=0) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.rowconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self._btn_starter['state']=tk.DISABLED
        self._lbl_starter=tk.StringVar()
        self._lbl_starter.set('--')
        self._btn_starter['textvariable']=self._lbl_starter
        self._btn_starter['height']=8
        self._btn_starter['width']=10
        self._btn_starter['relief']=tk.RIDGE
        
    def reset_widgets_for_new_deal(self):
        """
        Utility function called to put child widgets in appropriate state ahead of a new deal.
        :return None:
        """
        # Clear the starter card label
        self._lbl_starter.set('--')
        return None


class CribbageCribWidget(ttk.Labelframe, Subject):
    """
    Class represents a tkinter label frame, the widget contents of which will represent the crib in the application.
    """
    def __init__(self, parent) -> None:
        """
        :parameter parent: tkinter widget that is the parent of this widget
        """
        super().__init__(parent, text='Crib')
        Subject.__init__(self)
        
        # List of buttons representing cards in the crib
        self._btns_cards = []
        # List of StringVar control variables for the card labels
        self._lbls_cards = []

        self._btns_cards.append(tk.Button(self))
        self._btns_cards[0].grid(column=0, row=0) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.rowconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self._btns_cards[0]['state']=tk.DISABLED
        self._lbls_cards.append(tk.StringVar())
        self._lbls_cards[0].set('--')
        self._btns_cards[0]['textvariable']=self._lbls_cards[0]
        
        self._btns_cards.append(tk.Button(self))
        self._btns_cards[1].grid(column=1, row=0) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(1, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self._btns_cards[1]['state']=tk.DISABLED
        self._lbls_cards.append(tk.StringVar())
        self._lbls_cards[1].set('--')
        self._btns_cards[1]['textvariable']=self._lbls_cards[1]
        
        self._btns_cards.append(tk.Button(self))
        self._btns_cards[2].grid(column=2, row=0) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(2, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self._btns_cards[2]['state']=tk.DISABLED
        self._lbls_cards.append(tk.StringVar())
        self._lbls_cards[2].set('--')
        self._btns_cards[2]['textvariable']=self._lbls_cards[2]
        
        self._btns_cards.append(tk.Button(self))
        self._btns_cards[3].grid(column=3, row=0) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(3, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self._btns_cards[3]['state']=tk.DISABLED
        self._lbls_cards.append(tk.StringVar())
        self._lbls_cards[3].set('--')
        self._btns_cards[3]['textvariable']=self._lbls_cards[3]

        for b in self._btns_cards:
             b['height']=8
             b['width']=10
             b['relief']=tk.RIDGE

    def reset_widgets_for_new_deal(self):
        """
        Utility function called to put child widgets in appropriate state ahead of a new deal.
        :return None:
        """
        # Clear all current card lables in the crib widget
        for sv in self._lbls_cards: sv.set('--')
        return None


class CribbagePlayPileWidget(ttk.Labelframe, Subject):
    """
    Class represents a tkinter label frame, the widget contents of which will represent the pile of played cards visually in the application.
    """
    def __init__(self, parent) -> None:
        """
        :parameter parent: tkinter widget that is the parent of this widget
        """
        super().__init__(parent, text='Play Pile')
        Subject.__init__(self)
        
        # List of buttons representing cards in the play pile
        self._btns_cards = []
        # List of StringVar control variables for the card labels
        self._lbls_cards = []
        
        self._btns_cards.append(tk.Button(self))
        self._btns_cards[0].grid(column=0, row=0) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.rowconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self._btns_cards[0]['state']=tk.DISABLED
        self._lbls_cards.append(tk.StringVar())
        self._lbls_cards[0].set('--')
        self._btns_cards[0]['textvariable']=self._lbls_cards[0]

        self._btns_cards.append(tk.Button(self))
        self._btns_cards[1].grid(column=1, row=0) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(1, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.rowconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self._btns_cards[1]['state']=tk.DISABLED
        self._lbls_cards.append(tk.StringVar())
        self._lbls_cards[1].set('--')
        self._btns_cards[1]['textvariable']=self._lbls_cards[1]

        self._btns_cards.append(tk.Button(self))
        self._btns_cards[2].grid(column=2, row=0) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(2, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.rowconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self._btns_cards[2]['state']=tk.DISABLED
        self._lbls_cards.append(tk.StringVar())
        self._lbls_cards[2].set('--')
        self._btns_cards[2]['textvariable']=self._lbls_cards[2]

        self._btns_cards.append(tk.Button(self))
        self._btns_cards[3].grid(column=3, row=0) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(3, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.rowconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self._btns_cards[3]['state']=tk.DISABLED
        self._lbls_cards.append(tk.StringVar())
        self._lbls_cards[3].set('--')
        self._btns_cards[3]['textvariable']=self._lbls_cards[3]

        self._btns_cards.append(tk.Button(self))
        self._btns_cards[4].grid(column=4, row=0) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(4, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.rowconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self._btns_cards[4]['state']=tk.DISABLED
        self._lbls_cards.append(tk.StringVar())
        self._lbls_cards[4].set('--')
        self._btns_cards[4]['textvariable']=self._lbls_cards[4]
        
        self._btns_cards.append(tk.Button(self, text='--'))
        self._btns_cards[5].grid(column=5, row=0) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(5, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.rowconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self._btns_cards[5]['state']=tk.DISABLED
        self._lbls_cards.append(tk.StringVar())
        self._lbls_cards[5].set('--')
        self._btns_cards[5]['textvariable']=self._lbls_cards[5]

        self._btns_cards.append(tk.Button(self))
        self._btns_cards[6].grid(column=6, row=0) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(6, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.rowconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self._btns_cards[6]['state']=tk.DISABLED
        self._lbls_cards.append(tk.StringVar())
        self._lbls_cards[6].set('--')
        self._btns_cards[6]['textvariable']=self._lbls_cards[6]
        
        self._btns_cards.append(tk.Button(self))
        self._btns_cards[7].grid(column=7, row=0) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(7, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.rowconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self._btns_cards[7]['state']=tk.DISABLED
        self._lbls_cards.append(tk.StringVar())
        self._lbls_cards[7].set('--')
        self._btns_cards[7]['textvariable']=self._lbls_cards[7]
 
        self._btns_cards.append(tk.Button(self))
        self._btns_cards[8].grid(column=8, row=0) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(8, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.rowconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self._btns_cards[8]['state']=tk.DISABLED
        self._lbls_cards.append(tk.StringVar())
        self._lbls_cards[8].set('--')
        self._btns_cards[8]['textvariable']=self._lbls_cards[8]

        for b in self._btns_cards:
             b['height']=8
             b['width']=10
             b['relief']=tk.RIDGE
    
    def reset_widgets_for_new_deal(self):
        """
        Utility function called to put child widgets in appropriate state ahead of a new deal.
        :return None:
        """
        self.set_go_round_count()
        # Clear all current card lables in the crib widget
        for sv in self._lbls_cards: sv.set('--')
        return None

    def set_go_round_count(self, count=0):
        """
        Utility function to set the self Lableframe text.
        :parameter count: GO round count, integer
        :return: None
        """
        self['text']=f"Play Pile - GO round count = {count}"
        return None

class CribbageBoardWidget(ttk.Labelframe, Subject):
    """
    Class represents a tkinter label frame, the widget contents of which will represent the cribbage board visually in the application.
    """
    # TODO: Reserach if the player names need to be passed in and used, since the CribbageGameOutputEvents appear to carry the names as needed.
    def __init__(self, parent, name1='', name2='') -> None:
        """
        :parameter parent: tkinter widget that is the parent of this widget
        :parameter name1: Name of player 1 , string
        :parameter name2: Name of player 2 , string
        """
        super().__init__(parent, text='Cribbage Board')
        Subject.__init__(self)
        
        self._player1_track = ttk.Labelframe(self, text=f"{name1}")
        self._player1_track.grid(column=0, row=0, sticky='NWES') # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.rowconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx

        # Create a list of checkbuttons with indices 0-61 that represent visually the pegging locations along the player 1 track on the board
        self._player1_holes = []
        # Simultaneously, create a list of IntVar control variables that track the state of each checkbutton
        self._player1_pegs = []
        self._player1_track.columnconfigure(0, weight=1) # Grid-3 in Documentation\UI_WireFrame.pptx
        self._player1_track.columnconfigure(1, weight=1) # Grid-3 in Documentation\UI_WireFrame.pptx
        for i in range(0,31):
            self._player1_holes.append(ttk.Checkbutton(self._player1_track, text=str(i)))
            self._player1_holes[i].grid(column=0, row=(31-i)) # Grid-3 in Documentation\UI_WireFrame.pptx
            self._player1_track.rowconfigure((31-i), weight=1) # Grid-3 in Documentation\UI_WireFrame.pptx
            self._player1_holes[i]['state']=tk.DISABLED
            # Create and assign control variables
            self._player1_pegs.append(tk.IntVar())
            self._player1_holes[i]['variable'] = self._player1_pegs[i]
        for i in range(31,62):
            self._player1_holes.append(ttk.Checkbutton(self._player1_track, text=str(i)))
            self._player1_holes[i].grid(column=1, row=(i-30)) # Grid-3 in Documentation\UI_WireFrame.pptx
            self._player1_track.rowconfigure((i-30), weight=1) # Grid-3 in Documentation\UI_WireFrame.pptx
            self._player1_holes[i]['state']=tk.DISABLED
            # Create and assign control variables
            self._player1_pegs.append(tk.IntVar())
            self._player1_holes[i]['variable'] = self._player1_pegs[i]

        self._player2_track = ttk.Labelframe(self, text=f"{name2}")
        self._player2_track.grid(column=1, row=0, sticky='NWES') # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(1, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.rowconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx

        # Create a list of checkbuttons with indices 0-61 that represent visually the pegging locations along the player 2 track on the board
        self._player2_holes = []
        # Simultaneously, create a list of IntVar control variables that track the state of each checkbutton
        self._player2_pegs = []
        self._player2_track.columnconfigure(0, weight=1) # Grid-3 in Documentation\UI_WireFrame.pptx
        self._player2_track.columnconfigure(1, weight=1) # Grid-3 in Documentation\UI_WireFrame.pptx
        for i in range(0,31):
            self._player2_holes.append(ttk.Checkbutton(self._player2_track, text=str(i)))
            self._player2_holes[i].grid(column=0, row=(31-i)) # Grid-3 in Documentation\UI_WireFrame.pptx
            self._player2_track.rowconfigure((31-i), weight=1) # Grid-3 in Documentation\UI_WireFrame.pptx
            self._player2_holes[i]['state']=tk.DISABLED
            # Create and assign control variables
            self._player2_pegs.append(tk.IntVar())
            self._player2_holes[i]['variable'] = self._player2_pegs[i]
        for i in range(31,62):
            self._player2_holes.append(ttk.Checkbutton(self._player2_track, text=str(i)))
            self._player2_holes[i].grid(column=1, row=(i-30)) # Grid-3 in Documentation\UI_WireFrame.pptx
            self._player2_track.rowconfigure((i-30), weight=1) # Grid-3 in Documentation\UI_WireFrame.pptx
            self._player2_holes[i]['state']=tk.DISABLED
            # Create and assign control variables
            self._player2_pegs.append(tk.IntVar())
            self._player2_holes[i]['variable'] = self._player2_pegs[i]
        # Initialize so that both player's pegs start in pre-game positions (0 and 61)
        self.set_pegs_player1()
        self.set_pegs_player2()

    def set_pegs_player1(self, lead=0, trail=61):
        """
        Set the locations of the pegs on the board for player 1. By default places pegs in starting location.
        :parameter lead: Hole location of leading peg, int
        :parameter trail: Hole location of trailing peg, int
        :return None:
        """
        # Clear any existing peg locations
        for p in self._player1_pegs: p.set(0)
        # Set the new peg locatons
        self._player1_pegs[lead].set(1)
        self._player1_pegs[trail].set(1)
        return None

    def set_pegs_player2(self, lead=0, trail=61):
        """
        Set the locations of the pegs on the board for player 2. By default places pegs in starting location.
        :parameter lead: Hole location of leading peg, int
        :parameter trail: Hole location of trailing peg, int
        :return None:
        """
        # Clear any existing peg locations
        for p in self._player2_pegs: p.set(0)
        # Set the new peg locatons
        self._player2_pegs[lead].set(1)
        self._player2_pegs[trail].set(1)
        return None


class CribbageScoresInfoWidget(ttk.Labelframe, Subject):
    """
    Class represents a tkinter label frame, the widget contents of which will let the user interact with scoring combo information
    during play and during show.
    """
    def __init__(self, parent) -> None:
        """
        :parameter parent: tkinter widget that is the parent of this widget
        """
        super().__init__(parent, text='Scores Info')
        Subject.__init__(self)
        
        # Create a tree widget, to be used to interact with scoring information
        
        self._tree_scores = ttk.Treeview(self, columns=('player', 'while', 'combo','points','cards'), displaycolumns='#all', selectmode='browse', show='headings')
        self._tree_scores.grid(column=0, row=0, sticky='NWSE') # Grid-2 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx
        self.rowconfigure(0, weight=1) # Grid-2 in Documentation\UI_WireFrame.pptx

        self._tree_scores.heading('player',text='player')
        self._tree_scores.column('player',width=50)
        self._tree_scores.heading('while',text='while')
        self._tree_scores.column('while',width=50)
        self._tree_scores.heading('combo',text='combo')
        self._tree_scores.column('combo',width=50)
        self._tree_scores.heading('points',text='points')
        self._tree_scores.column('points',width=50)
        self._tree_scores.heading('cards',text='cards')
        self._tree_scores.column('cards',width=50)

        # Create a vertical Scrollbar and associate it with _tree_scores
        self._scrollbar_vert = ttk.Scrollbar(self, command=self._tree_scores.yview)
        self._scrollbar_vert.grid(column=1, row=0, rowspan=2, sticky='NWSE')
        self._tree_scores['yscrollcommand'] = self._scrollbar_vert.set

        # Create a horizontal Scrollbar and associate it with _tree_scores
        self._scrollbar_horz = ttk.Scrollbar(self, command=self._tree_scores.xview, orient=tk.HORIZONTAL)
        self._scrollbar_horz.grid(column=0, row=1, columnspan=2, sticky='NWSE')
        self._tree_scores['xscrollcommand'] = self._scrollbar_horz.set
        
    def add_scoring_combo_info(self, player='', _while='', combo_info=[]):
        """
        Utility function called to add an entry to the score info widget.
        :parameter player: Name of the player who scored, string
        :parameter _while: What is happening in the game that led to the score? (e.g., drawing starter, playing, showing), string
        :parameter combo_info: Scoring combo list, list of CribbageComboInfo objects
        :return: None
        """
        for item in combo_info:
            for instance in item.instance_list:
                self._tree_scores.insert('', 'end', values=(player, _while, item.combo_name, int(item.score/item.number_instances),
                                                            self._card_list_to_string(instance)))
        return None
    
    def _card_list_to_string(self, card_list=[]):
        """
        Utility method that converts the argument list of cards to a string of form 'KH, 5D, ...'.
        :parameter card_list: List of Card objects
        :return cards_string: String representing the list of cards, of form 'kH, 5D, ...'
        """
        cards_string = ''
        for card in card_list:
            cards_string += f"{str(card)} "
        if len(card_list) > 0:
            # Remove unneeded trailing space
            cards_string = cards_string[0:len(cards_string)-1]
        return cards_string

    def reset_widgets_for_new_deal(self):
        """
        Utility function called to put child widgets in appropriate state ahead of a new deal.
        :return: None
        """
        # Clear the contents of the tree
        top_iids = self._tree_scores.get_children()
        for iid in top_iids:
            self._tree_scores.delete(iid)
        return None
    
    # TODO: Do we really want to clear the scores for a new go round, or just for a new deal? At the moment, this isn't
    # called from anywhere, so effectively does nothing.
    def reset_widgets_for_new_go_round(self):
        """
        Utility function called to put child widgets in appropriate state ahead of a new go round.
        :return: None
        """
        # Clear the contents of the tree
        top_iids = self._tree_scores.get_children()
        for iid in top_iids:
            self._tree_scores.delete(iid)        
        return None
