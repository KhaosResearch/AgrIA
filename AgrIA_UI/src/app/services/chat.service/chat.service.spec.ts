import { TestBed } from '@angular/core/testing';

import { ChatService } from './chat.service';

import { provideHttpClient } from '@angular/common/http';

import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

describe('ChatService', () => {
  let service: ChatService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(ChatService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('loadParcelDataToChat should append thread_id to the request', () => {
    const formData = new FormData();
    formData.append('imageDate', '01/2024');
    formData.append('lang', 'es');

    service.loadParcelDataToChat(formData, 'session_test_123').subscribe();

    const req = httpMock.expectOne(
      req => req.url.endsWith('/load-parcel-data-to-chat') && req.method === 'POST'
    );
    expect(req.request.body).toBe(formData);
    expect(formData.get('thread_id')).toBe('session_test_123');

    req.flush({ response: { text: 'ok', imageDesc: { es: 'ctx' } } });
  });
});
