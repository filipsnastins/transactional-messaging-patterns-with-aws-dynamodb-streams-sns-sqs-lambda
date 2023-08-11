Feature: Reserve customer credit for a new order

    Background:
        Given customer exists with credit limit of "249.99"

    Scenario: Reserve credit for a new order
        When order created with total amount of "149.99"
        Then CustomerCreditReserved event is published
        And the customer available credit is "100.00"

    Scenario: Credit limit exceeded
        When order created with total amount of "300.00"
        Then the CustomerCreditReservationFailed event is published
        And the customer available credit is "249.99"

    Scenario: Reserve credit for not existing customer
        When order is created for not existing customer
        Then the CustomerValidationFailed event is published - "CUSTOMER_NOT_FOUND"
