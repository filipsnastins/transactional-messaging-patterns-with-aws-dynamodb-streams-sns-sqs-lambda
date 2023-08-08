Feature: Order credit check

    Scenario: Credit check passed for a new order
        Given an order in "PENDING" state
        When CustomerCreditReserved event is received
        Then the order state is "APPROVED"
        And the OrderApproved event is sent

    Scenario: Credit check failed for a new order
        Given an order in "PENDING" state
        When CustomerCreditReservationFailed event is received
        Then the order state is "REJECTED"
        And the OrderRejected event is sent
