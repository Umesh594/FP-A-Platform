import { createElement } from 'lwc';
import FpaPipelineSummary from 'c/fpaPipelineSummary';
import getPipelineSummary from '@salesforce/apex/FpaPipelineController.getPipelineSummary';
import { registerApexTestWireAdapter } from '@salesforce/sfdx-lwc-jest';

const getPipelineSummaryAdapter = registerApexTestWireAdapter(getPipelineSummary);

describe('c-fpa-pipeline-summary', () => {
  it('renders returned pipeline metrics', async () => {
    const element = createElement('c-fpa-pipeline-summary', { is: FpaPipelineSummary });
    document.body.appendChild(element);
    getPipelineSummaryAdapter.emit({ accountCount: 3, openOpportunityCount: 2, totalPipelineAmount: 2090000, weightedPipelineAmount: 1337000 });
    await Promise.resolve();
    expect(element.shadowRoot.textContent).toContain('3 accounts');
  });
});
