@IsTest
private class FpaPipelineControllerTest {
    @TestSetup
    static void setupData() {
        Account account = new Account(Name = 'Acme Finance', Industry = 'Financial Services');
        insert account;
        insert new Opportunity(Name = 'FP&A Renewal', AccountId = account.Id, StageName = 'Proposal/Price Quote', CloseDate = Date.today().addDays(30), Amount = 100000, Probability = 60);
    }

    @IsTest
    static void returnsPipelineMetrics() {
        Test.startTest();
        FpaPipelineController.PipelineSummary summary = FpaPipelineController.getPipelineSummary();
        Test.stopTest();
        System.assertEquals(1, summary.accountCount);
        System.assertEquals(1, summary.openOpportunityCount);
        System.assertEquals(100000, summary.totalPipelineAmount);
        System.assertEquals(60000, summary.weightedPipelineAmount);
    }

    @IsTest
    static void rejectsShortSoslTermsAndPublishesEvent() {
        System.assertEquals(0, FpaPipelineController.searchAccounts('a').size());
        Test.startTest();
        Boolean accepted = FpaPipelineController.publishPipelineSync(1, 1, 60000);
        Test.stopTest();
        System.assertEquals(true, accepted);
    }
}
