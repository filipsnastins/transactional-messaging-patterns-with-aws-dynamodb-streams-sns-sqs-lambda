Feature: Create order

    Scenario: Create new order
        Given an order data with total amount of "123.99"
        When order creation is requested
        Then the order creation request succeeded
        And the order state is "PENDING"
        And the OrderCreated event is sent
