import { TestBed } from '@angular/core/testing';

import { ChatAssistantService } from './chat-assistant.service';

import { provideHttpClient } from '@angular/common/http';

import { provideHttpClientTesting } from '@angular/common/http/testing';

import { TranslateModule, TranslateLoader } from '@ngx-translate/core';

import { Observable, of } from 'rxjs';

/**
 * Init the TranslateModule with TranslateLoader to empty
 */
export class MockTranslateLoader implements TranslateLoader {
  getTranslation(lang: string): Observable<any> {
    return of({});
  }
}

describe('ChatAssistantService', () => {
  let service: ChatAssistantService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting()
      ],
    });
    service = TestBed.inject(ChatAssistantService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
