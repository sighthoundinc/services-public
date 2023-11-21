import { writable, type Writable } from 'svelte/store';

interface SioParameters {
    VIDEO_IN: string;
    sourceId: string;
    recordTo: string;
    imageSaveDir: string;
    amqpHost: string;
    amqpPort: string;
    amqpExchange: string;
    amqpUser: string;
    amqpPassword: string;
    amqpErrorOnFailure: string;
    [extraParameter: string]: any;
  }
  
  interface PipelineData {
    pipeline: string;
    parameters: SioParameters;
  }
  
  interface Pipeline {
    data: PipelineData;
    status: string;
    lastStatusUpdate: number;
    lastUpdate: number;
    created: number;
    source: string;
  }
  

interface Pipelines {
  [key: string]: Pipeline;
}

export const pipelines: Writable<Pipelines> = writable({});

const defaultDeviceUrl = "";
export const deviceUrl = writable(defaultDeviceUrl);
export const aqueductUrl = writable(`http://${defaultDeviceUrl}:8888`);
export const mcpUrl = writable(`http://${defaultDeviceUrl}:9097`);

export function updateDeviceUrl(url: string) {
  deviceUrl.set(url);
  aqueductUrl.set(`http://${url}:8888`);
  mcpUrl.set(`http://${url}:9097`);
}