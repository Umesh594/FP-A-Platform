import { createElement } from 'lwc';
import WorkforcePlanSummary from 'c/workforcePlanSummary';
import { registerApexTestWireAdapter } from '@salesforce/sfdx-lwc-jest';
import getApprovedWorkforcePlans from '@salesforce/apex/WorkforcePlanningController.getApprovedWorkforcePlans';
const adapter = registerApexTestWireAdapter(getApprovedWorkforcePlans);
describe('c-workforce-plan-summary', () => {
  afterEach(() => document.body.innerHTML = '');
  it('renders approved workforce-plan data', async () => {
    const element = createElement('c-workforce-plan-summary', { is: WorkforcePlanSummary });
    document.body.appendChild(element);
    adapter.emit([{ department: 'Engineering', requestedHeadcount: 3, monthlyPlannedCost: 36000 }]);
    await Promise.resolve();
    expect(element.shadowRoot.querySelector('lightning-datatable')).not.toBeNull();
  });
});
