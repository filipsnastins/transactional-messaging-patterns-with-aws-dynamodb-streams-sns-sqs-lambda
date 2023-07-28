Feature: Credit limit

    Scenario Outline:
        Given customer exists with name "John Doe" and credit limit "249.99"

    Scenario: Credit reservation for a new order
        When order created with total "149.99"
        Then the customer credit limit reserved event is published
        And the customer's available credit is "100.00"

    Scenario: Credit limit exceeded
        When order created with total "300.00"
        Then the customer credit limit exceeded event is published
        And the customer available credit is "249.99"

    Scenario: Credit reservation for non-existing customer
        When order is created for non-existing customer
        Then the customer validation failed event is published
