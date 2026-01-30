import pytest
import numpy as np
from datetime import datetime

from finmetry.constants import Order, ORDERTYPE
from finmetry.strategy_handler.base import MarketGraphData, StockData


@pytest.fixture
def simple_market():
    ts = np.datetime64("2024-01-01")

    stock = StockData(
        symbol="AAPL",
        open=100.0,
        high=110.0,
        low=90.0,
        close=105.0,
        volume=1000,
        timestamp=ts,
        features=None,
    )

    return MarketGraphData(
        timestamp=ts,
        stocks={"AAPL": stock},
    )


@pytest.fixture
def buy_order():
    return Order(
        id="order-1",
        symbol="AAPL",
        value_frac=0.5,
        price=100.0,
        timestamp=np.datetime64("2024-01-01"),
        order_type=ORDERTYPE.buy,
        account_idx=0,
    )



def test_account_buy_reduces_cash_and_creates_holding(simple_market, buy_order):
    from finmetry.portfolio_handler import Account
    from finmetry.executioners import ExecutionModel

    acc = Account(account_idx=0, starting_cash=2000.0, executioner=ExecutionModel())
    acc.on_order(buy_order)

    assert acc.cash == 1000.0
    assert "order-1" in acc.holdings

    h = acc.holdings["order-1"]
    assert h["qty"] == 10
    assert h["entry_price"] == 100.0


def test_mark_to_market_updates_ltp(simple_market, buy_order):
    from finmetry.portfolio_handler import Account
    from finmetry.executioners import ExecutionModel

    acc = Account(account_idx=0, starting_cash=2000.0, executioner=ExecutionModel())
    acc.on_order(buy_order)

    acc.mark_to_market(simple_market)

    h = acc.holdings["order-1"]
    assert h["ltp"] == 105.0

    snap = acc.account_history[-1]
    assert snap["holdings_value"] == 1050.0


def test_exit_order_closes_holding(simple_market):
    from finmetry.portfolio_handler import Account
    from finmetry.executioners import ExecutionModel

    acc = Account(account_idx=0, starting_cash=2000.0, executioner=ExecutionModel())

    buy = Order(
        id="order-1",
        symbol="AAPL",
        value_frac=0.5,
        price=100.0,
        timestamp=simple_market.timestamp,
        order_type=ORDERTYPE.buy,
        account_idx=0,
    )
    acc.on_order(buy)

    holding = acc.holdings["order-1"]
    exit_price = 110.0

    sell = Order(
        id="order-1",
        symbol="AAPL",
        fill_qty=holding["qty"],
        price=110.0,
        timestamp=simple_market.timestamp,
        order_type=ORDERTYPE.sell,
        account_idx=0,
    )
    acc.on_order(sell)

    assert acc.holdings == {}
    assert acc.cash == 2000.0 + 100.0


def test_accounts_are_isolated(simple_market):
    from finmetry.portfolio_handler import Portfolio
    from finmetry.executioners import ExecutionModel


    pf = Portfolio(starting_cash=2000.0, executioner=ExecutionModel(), total_accounts=2)

    pf.on_order(Order(
        id="o1",
        symbol="AAPL",
        value_frac=0.5,
        price=100.0,
        timestamp=simple_market.timestamp,
        order_type=ORDERTYPE.buy,
        account_idx=0,
    ))

    pf.on_order(Order(
        id="o2",
        symbol="AAPL",
        value_frac=1.0,
        price=100.0,
        timestamp=simple_market.timestamp,
        order_type=ORDERTYPE.buy,
        account_idx=1,
    ))

    assert pf.accounts[0].cash == 500.0
    assert pf.accounts[1].cash == 0.0
