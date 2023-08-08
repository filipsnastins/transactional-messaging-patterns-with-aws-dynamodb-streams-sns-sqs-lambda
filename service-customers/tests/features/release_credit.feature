Feature: Release customer credit when an order is cancelled

    Background:
        Given customer exists with credit limit "249.99"

    Scenario: Release credit when order is cancelled
        Given order created with total "149.99"
        And the customer credit is reserved
        And the customer available credit is "100.00"
        When order is cancelled
        Then the customer available credit is "249.99"
