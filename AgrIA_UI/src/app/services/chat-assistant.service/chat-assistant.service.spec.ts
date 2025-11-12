import { TestBed } from '@angular/core/testing';

import { ChatAssistantService } from './chat-assistant.service';

describe('ChatAssistantService', () => {
  let service: ChatAssistantService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ChatAssistantService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
