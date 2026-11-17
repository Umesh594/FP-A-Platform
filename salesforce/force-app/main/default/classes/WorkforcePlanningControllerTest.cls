@IsTest
private class WorkforcePlanningControllerTest {
    @IsTest
    static void rejectsInvalidApprovalPayloadAndPublishesValidEvent() {
        insert new Headcount_Plan__c(Department__c = 'Engineering', Effective_Month__c = Date.newInstance(2026, 11, 1), Requested_Headcount__c = 3, Monthly_Planned_Cost__c = 36000, Approval_Status__c = 'Approved');
        System.assertEquals(1, WorkforcePlanningController.getApprovedWorkforcePlans().size());
        try {
            WorkforcePlanningController.publishApprovedPlan('', Date.today(), 1, 1000);
            System.assert(false, 'Expected input validation failure');
        } catch (AuraHandledException expected) {
            System.assert(expected.getMessage().contains('valid department'));
        }
        Test.startTest();
        Boolean accepted = WorkforcePlanningController.publishApprovedPlan('Engineering', Date.newInstance(2026, 11, 1), 3, 36000);
        Test.stopTest();
        System.assertEquals(true, accepted);
    }
}
