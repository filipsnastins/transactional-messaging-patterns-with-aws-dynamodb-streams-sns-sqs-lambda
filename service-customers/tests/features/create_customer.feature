Feature: Create customer

    Scenario: Create new customer with clean available credit
        Given customer with name "John Doe" and credit limit "249.99"
        When customer creation is requested
        Then the customer creation request is successful
        And the customer is created with correct data and available credit of "249.99"

    Scenario: Customer not found
        When not existing customer is queried
        Then the customer is not found
