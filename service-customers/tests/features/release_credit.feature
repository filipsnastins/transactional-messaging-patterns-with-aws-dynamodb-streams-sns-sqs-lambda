Feature: Release customer credit when an order is canceled

    Background:
        Given customer exists with credit limit "249.99"

    Scenario: Release credit when order is canceled
        Given order created with total "149.99"
        When order is canceled
        When the customer credit is "249.99"

    Scenario: Release credit for non-existing customer
        When order is canceled
        Then the customer validation fails - customer not found
