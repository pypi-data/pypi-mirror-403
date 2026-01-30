"""
This module defines CribbageApp class, which is an subclass of tkSimulatorApp from the tkApp framework. The cribbage application is a
tkinter-based GUI application for playing the card game Cribbage. The application uses a CribbageGameAdapter to interface with the CribbageGame logic.
The CribbageGame class and related classes are part of the CribbageSim package.

Exported Classes:
    CribbageApp -- Subclass of tkSimulatorApp extended to work with the CribbageGame from the CribbageSim package.
    CribbageGameAdapter -- Adapter class to wrap CribbageGame object for the SimulatorModel class.

Exported Exceptions:
    None    
 
Exported Functions:
    None

Scripting:
    To run the CribbageApp, execute this module as the main program. This will create an instance of the CribbageApp and start its event loop.

Logging:
    The SimulatorModel class captures logging from the logger named 'cribbage_logger', which is set up by the
    CribbageSimulator class from the CribbageSim package.
"""


# standard imports
import tkinter as tk
import sysconfig
import logging


# local imports
from CribbageSim.CribbageSimulator import CribbageSimulator
from CribbageSim.CribbageGame import CribbageGame
from CribbageSim.CribbagePlayStrategy import InteractiveCribbagePlayStrategy, HoyleishDealerCribbagePlayStrategy, HoyleishPlayerCribbagePlayStrategy
from tkAppFramework.sim_adapter import SimulatorAdapter
from tkAppFramework.tkSimulatorApp import tkSimulatorApp, AppAboutInfo
from pyCribbageApp.tkCribbageViewManager import tkCribbageViewManager


class CribbageGameAdapter(SimulatorAdapter):
    """
    Adapter to wrap Cribbage object for the SimulatorModel class.
    """
    def __init__(self, out_queue=None):
        """
        :parameter out_queue: Queue object to which simulator output messages (logging LogRecords) are posted.
        """
        super().__init__(CribbageGame(player_strategy1 = InteractiveCribbagePlayStrategy(), player_strategy2 = HoyleishPlayerCribbagePlayStrategy(),
                                      dealer_strategy2 = HoyleishDealerCribbagePlayStrategy()), 'cribbage_logger', out_queue)

    def run(self):
        """
        Launch a cribbage game.
        :return: None
        """
        self.simulator.play()
        return None

    def load_and_run(self):
        """
        Launch a cribbage game, instructing it to load a saved game.
        :return: None
        """
        self.simulator.play(load_game=True)
        return None


class CribbageApp(tkSimulatorApp):
    """
    Class represent a Cribbage application built using the tkAppFramework package, and tkinter. It is a subclass of tkSimulatorApp.
    """
    def __init__(self, parent, log_level = logging.INFO) -> None:
        """
        :parameter parent: The top-level tkinter widget, typicaly the return value from tkinter.Tk()
        :param log_level: The logging level to set for the logger, e.g., logging.DEBUG, logging.INFO, etc.
        """
        help_file_path = sysconfig.get_path('data') + '\\Help\\pyCribbageApp\\pyCribbageApp_HelpFile.txt'
        info = AppAboutInfo(name='Cribbage Application', version='0.1.3', copyright='2026', author='Kevin R. Geurts',
                                license='MIT License', source='https://github.com/KevinRGeurts/pyCribbageApp',
                                help_file=help_file_path)
        super().__init__(parent, title = 'Cribbage Application', app_info = info, log_level = log_level)
        
    def _setup_child_widgets(self):
        """
        Utility function of tkApp class extended first ty tkSimulatorApp, and then here to set up tkCribbageViewManager. 
        :return: None
        """
        super()._setup_child_widgets()

        # Adjust grid setting for self._view_manager, since we want it to appear at the bottom of the window
        self._view_manager.grid(column=0, row=2, sticky='NWES') # Grid-1 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(0, weight=1) # Grid-1 in Documentation\UI_WireFrame.pptx
        self.rowconfigure(2, weight=1) # Grid-1 in Documentation\UI_WireFrame.pptx

        # Setup for tkCribbageViewManager
        self._cribbage_view_manager = tkCribbageViewManager(self, 'Player 1', 'Player 2')
        # Attach cribbage view manager as observer of model, because tkViewManager.onDestroy() will attempt detach
        self.getModel().attach(self._cribbage_view_manager)
        self._cribbage_view_manager.grid(column=0, row=1, sticky='NWES') # Grid-1 in Documentation\UI_WireFrame.pptx
        self.columnconfigure(0, weight=1) # Grid-1 in Documentation\UI_WireFrame.pptx
        self.rowconfigure(1, weight=1) # Grid-1 in Documentation\UI_WireFrame.pptx
        
        return None


if __name__ == '__main__':
    """
    Launch tkinter-based CribbageApp.
    """
    
    # Set up logging for the CribbageSimulator
    CribbageSimulator().setup_logging(False)    
    
    # Get Tcl interpreter up and running and get the root widget
    root = tk.Tk()
    # Create the cribbage app
    simapp = CribbageApp(root)
    # Create and set the CribbageGameAdapter into the tkSimulatorApp's SimulatorModel
    simapp.getModel().sim_adapter = CribbageGameAdapter(simapp.sim_output_queue)
    # Start the app's event loop running
    simapp.mainloop()