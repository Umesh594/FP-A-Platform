import { LightningElement, wire } from 'lwc';
import getPipelineSummary from '@salesforce/apex/FpaPipelineController.getPipelineSummary';
import publishPipelineSync from '@salesforce/apex/FpaPipelineController.publishPipelineSync';

export default class FpaPipelineSummary extends LightningElement {
  @wire(getPipelineSummary) summary;

  async handlePublish() {
    const data = this.summary.data;
    if (!data) return;
    await publishPipelineSync({
      accountCount: data.accountCount,
      opportunityCount: data.openOpportunityCount,
      weightedPipelineAmount: data.weightedPipelineAmount,
    });
  }
}
