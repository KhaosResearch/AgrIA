import { TestBed } from '@angular/core/testing';

import { AppComponent } from './app.component';

import { provideHttpClient } from '@angular/common/http';

import { provideHttpClientTesting } from '@angular/common/http/testing';

import { TranslateModule, TranslateLoader } from '@ngx-translate/core';

import { provideRouter } from '@angular/router';

import { Observable, of } from 'rxjs';

// Mock
class MockTranslateLoader implements TranslateLoader {
  getTranslation(lang: string): Observable<any> {
    return of({});
  }
}
describe('AppComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        AppComponent, // <--- Import the Standalone Component
        TranslateModule.forRoot({
          loader: { provide: TranslateLoader, useClass: MockTranslateLoader },
        }),
      ],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
      ],
    }).compileComponents();
  });

  // Test 1: App creates successfully
  it('should create the app', () => {
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });
  
  // Test 2: Check the ACTUAL title property defined in your .ts file
  it(`should have the 'AgrIA - Agricultural Imaging Assistant' title`, () => {
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.componentInstance;
    expect(app.title).toEqual('AgrIA - Agricultural Imaging Assistant');
  });
  
  // Test 3: Check that the Navbar is rendered (instead of looking for a missing h1)
  it('should render the navbar', () => {
    const fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges(); // Trigger change detection to render HTML
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('app-navbar')).toBeTruthy();
  });
});
