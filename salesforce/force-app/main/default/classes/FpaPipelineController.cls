public with sharing class FpaPipelineController {
    public class PipelineSummary {
        @AuraEnabled public Integer accountCount;
        @AuraEnabled public Integer openOpportunityCount;
        @AuraEnabled public Decimal totalPipelineAmount;
        @AuraEnabled public Decimal weightedPipelineAmount;

        public PipelineSummary(Integer accountCount, Integer openOpportunityCount, Decimal totalPipelineAmount, Decimal weightedPipelineAmount) {
            this.accountCount = accountCount;
            this.openOpportunityCount = openOpportunityCount;
            this.totalPipelineAmount = totalPipelineAmount;
            this.weightedPipelineAmount = weightedPipelineAmount;
        }
    }

    @AuraEnabled(cacheable=true)
    public static PipelineSummary getPipelineSummary() {
        Integer accounts = [SELECT COUNT() FROM Account];
        AggregateResult[] results = [
            SELECT COUNT(Id) opportunityCount, SUM(Amount) totalAmount, SUM(Amount * Probability / 100) weightedAmount
            FROM Opportunity
            WHERE IsClosed = false
        ];
        AggregateResult result = results[0];
        return new PipelineSummary(
            accounts,
            (Integer) result.get('opportunityCount'),
            (Decimal) result.get('totalAmount'),
            (Decimal) result.get('weightedAmount')
        );
    }

    @AuraEnabled(cacheable=true)
    public static List<Account> searchAccounts(String searchTerm) {
        if (String.isBlank(searchTerm) || searchTerm.trim().length() < 2) {
            return new List<Account>();
        }
        String escaped = String.escapeSingleQuotes(searchTerm.trim());
        List<List<SObject>> results = Search.query('FIND {\'' + escaped + '*\' IN NAME FIELDS RETURNING Account(Id, Name, Industry, AnnualRevenue LIMIT 10)');
        return (List<Account>) results[0];
    }

    @AuraEnabled
    public static Boolean publishPipelineSync(Integer accountCount, Integer opportunityCount, Decimal weightedPipelineAmount) {
        Database.SaveResult result = EventBus.publish(new Fpa_Pipeline_Sync__e(
            Account_Count__c = accountCount,
            Opportunity_Count__c = opportunityCount,
            Weighted_Pipeline__c = weightedPipelineAmount,
            Source__c = 'LWC'
        ));
        if (!result.isSuccess()) {
            throw new AuraHandledException('Unable to publish pipeline sync event');
        }
        return true;
    }
}
