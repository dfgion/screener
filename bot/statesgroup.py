from aiogram.fsm.state import State, StatesGroup

class MenuStatesGroup(StatesGroup):
    percent_long = State()
    percent_short = State()
    timeframe_long = State()
    timeframe_short = State()
    menu = State()
    
class ChangeStatesGroup(StatesGroup):
    change_long = State()
    change_short = State()
    change_time_long = State()
    change_time_short = State()