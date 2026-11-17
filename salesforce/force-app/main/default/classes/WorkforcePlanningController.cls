public with sharing class WorkforcePlanningController {
    public class WorkforceMetric {
        @AuraEnabled public String department;
        @AuraEnabled public Decimal requestedHeadcount;
        @AuraEnabled public Decimal monthlyPlannedCost;
        public WorkforceMetric(String department, Decimal requestedHeadcount, Decimal monthlyPlannedCost) {
            this.department = department;
            this.requestedHeadcount = requestedHeadcount;
            this.monthlyPlannedCost = monthlyPlannedCost;
        }
    }

    @AuraEnabled(cacheable=true)
    public static List<WorkforceMetric> getApprovedWorkforcePlans() {
        List<AggregateResult> rows = [
            SELECT Department__c department, SUM(Requested_Headcount__c) headcount, SUM(Monthly_Planned_Cost__c) cost
            FROM Headcount_Plan__c WHERE Approval_Status__c = 'Approved' GROUP BY Department__c LIMIT 50
        ];
        List<WorkforceMetric> metrics = new List<WorkforceMetric>();
        for (AggregateResult row : rows) metrics.add(new WorkforceMetric((String) row.get('department'), (Decimal) row.get('headcount'), (Decimal) row.get('cost')));
        return metrics;
    }

    @AuraEnabled
    public static Boolean publishApprovedPlan(String department, Date effectiveMonth, Integer requestedHeadcount, Decimal monthlyPlannedCost) {
        if (String.isBlank(department) || effectiveMonth == null || requestedHeadcount == null || requestedHeadcount < 0 || monthlyPlannedCost == null || monthlyPlannedCost < 0) {
            throw new AuraHandledException('A valid department, month, headcount, and monthly planned cost are required.');
        }
        Database.SaveResult result = EventBus.publish(new Workforce_Plan_Approved__e(Department__c = department.trim(), Effective_Month__c = effectiveMonth, Requested_Headcount__c = requestedHeadcount, Monthly_Planned_Cost__c = monthlyPlannedCost));
        if (!result.isSuccess()) throw new AuraHandledException('Unable to publish workforce approval event.');
        return true;
    }
}
