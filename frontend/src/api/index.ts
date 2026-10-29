import { realApi } from './client';
import { mockApi } from './mockClient';

const useMock = import.meta.env.VITE_USE_MOCK !== 'false';
export const isDemoMode = useMock;
export const api = useMock ? mockApi : realApi;
