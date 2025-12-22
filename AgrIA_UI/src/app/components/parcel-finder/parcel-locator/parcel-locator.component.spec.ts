import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ParcelLocatorComponent } from './parcel-locator.component';

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

describe('ParcelLocatorComponent', () => {
  let component: ParcelLocatorComponent;
  let fixture: ComponentFixture<ParcelLocatorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        ParcelLocatorComponent, 
        TranslateModule.forRoot({
          loader: { provide: TranslateLoader, useClass: MockTranslateLoader },
        }),
      ],
      providers: [
        provideHttpClient(), 
        provideHttpClientTesting()
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ParcelLocatorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
