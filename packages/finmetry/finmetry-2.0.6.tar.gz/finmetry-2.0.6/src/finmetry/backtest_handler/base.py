from typing import List

from ..portfolio_handler import Portfolio
from ..executioners import ExecutionModel
from ..strategy_handler import StgDataLoader, StrategyBase
from ..constants import ZeroQtyError

class Backtester:
    def __init__(self, data_loader: StgDataLoader, strategy: StrategyBase, portfolio: Portfolio):
        self.data_loader = data_loader
        self.strategy = strategy
        self.portfolio = portfolio

    def run(self, skip_zero_qty_error:bool=True):
        for market_data in self.data_loader:
            entry_orders = self.strategy(market_data)
            exit_orders = self.portfolio.get_exit_orders(market_data)
            ### keeping exit_orders first to avoid cash going negative
            all_orders = exit_orders + entry_orders
            for order in all_orders:
                try:
                    self.portfolio.on_order(order)
                except ZeroQtyError:
                    pass
            self.portfolio.mark_to_market(market_data)
