export interface IChatMessage {
  role: 'user' | 'model';
  content: string;
  loading?: boolean;
  revealProgress?: string;
  /**
   * When set, this text is shown in the chat bubble instead of `content`.
   * Used for system commands (e.g. CAP routing tags) where the backend
   * receives the tag but the user sees a human-readable label.
   */
  displayContent?: string;
}

export interface IChatAssistantResponse {
  message: string;
  error?: string;
}
