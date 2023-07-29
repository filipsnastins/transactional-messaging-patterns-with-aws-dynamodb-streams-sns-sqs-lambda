Feature: Create customer

    Scenario: Create new customer with full available credit
        Given customer with name "John Doe" and credit limit "249.99"
        When customer creation is requested
        Then the customer creation request is successful
        And the customer is created with correct data and full available credit

    Scenario: Customer not found
        When customer with ID "12b38f68-2d61-4cb2-8661-773c40702815" is queried
        Then the customer is not found
