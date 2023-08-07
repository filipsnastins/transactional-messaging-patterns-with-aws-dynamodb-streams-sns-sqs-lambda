Feature: Reserve customer credit for a new order

    Background:
        Given customer exists with credit limit "249.99"

    Scenario: Credit reservation for a new order
        When order created with total "149.99"
        Then the customer credit is reserved
        And the customer available credit is "100.00"

    Scenario: Credit limit exceeded
        When order created with total "300.00"
        Then the customer credit reservation fails
        And the customer available credit is "249.99"

    Scenario: Credit reservation for non-existing customer
        When order is created for non-existing customer
        Then the customer validation fails - customer not found
