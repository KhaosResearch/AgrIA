export interface IChatMessage {
  role: 'user' | 'model';
  content: string;
  loading?: boolean;
  revealProgress?: string;
}

export interface IChatAssistantResponse {
  message: string;
  error?: string;
}
