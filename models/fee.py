class FeeModel:
    def __init__(self, maker_fee_rate: float, taker_fee_rate: float):
        self.maker_fee_rate = maker_fee_rate
        self.taker_fee_rate = taker_fee_rate
    
    def calculate_expected_fees(self, maker_proportion: float, taker_proportion: float, quantity_usd: float) -> float:
        """
        Calculate the expected fees using a rule-based fee model.
        
        :param maker_proportion: Proportion of orders placed by makers.
        :param taker_proportion: Proportion of orders placed by takers.
        :param quantity_usd: The USD equivalent quantity of the order.
        
        :return: Calculated fee value.
        """
        maker_fee = maker_proportion * self.maker_fee_rate * quantity_usd
        taker_fee = taker_proportion * self.taker_fee_rate * quantity_usd
        total_fee = maker_fee + taker_fee
        
        return total_fee
