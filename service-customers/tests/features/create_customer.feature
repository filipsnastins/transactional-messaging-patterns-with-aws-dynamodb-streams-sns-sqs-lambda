Feature: Create customer

    Scenario: Create new customer with clean available credit
        Given a customer data with credit limit of "249.99"
        When customer creation is requested
        Then the customer creation request succeeded
        And the customer is created
        And the customer available credit is "249.99"
        And the CustomerCreated event is published

    Scenario: Customer not found
        When not existing customer is queried
        Then the customer is not found
