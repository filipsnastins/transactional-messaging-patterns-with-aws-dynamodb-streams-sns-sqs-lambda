Feature: Create customer

    Scenario: Create new customer with full available credit
        Given customer with name "John Doe" and credit limit "200.00"
        When customer creation is requested
        Then the customer is created successfully
        And the customer is created with correct data and full available credit
