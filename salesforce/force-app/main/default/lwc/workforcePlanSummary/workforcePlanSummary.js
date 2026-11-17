import { LightningElement, wire } from 'lwc';
import getApprovedWorkforcePlans from '@salesforce/apex/WorkforcePlanningController.getApprovedWorkforcePlans';

export default class WorkforcePlanSummary extends LightningElement {
  columns = [
    { label: 'Department', fieldName: 'department' },
    { label: 'Planned Headcount', fieldName: 'requestedHeadcount', type: 'number' },
    { label: 'Monthly Planned Cost', fieldName: 'monthlyPlannedCost', type: 'currency' },
  ];
  @wire(getApprovedWorkforcePlans) plans;
  get hasPlans() { return Array.isArray(this.plans.data) && this.plans.data.length > 0; }
}
