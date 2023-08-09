Feature: Create order

    Scenario: Create new order
        Given an order data with total amount of "123.99"
        When order creation is requested
        Then the order is created with state "PENDING"
        And the OrderCreated event is published
