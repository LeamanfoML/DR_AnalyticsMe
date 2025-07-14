def calculate_profit(buy_price, sell_price, buy_commission, sell_commission, transfer_fee):
    net_sell_price = sell_price * (1 - sell_commission)
    total_buy_cost = buy_price * (1 + buy_commission) + transfer_fee
    return net_sell_price - total_buy_cost
