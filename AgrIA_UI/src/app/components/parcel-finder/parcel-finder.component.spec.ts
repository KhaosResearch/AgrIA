import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ParcelFinderComponent } from './parcel-finder.component';

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

describe('ParcelFinderComponent', () => {
  let component: ParcelFinderComponent;
  let fixture: ComponentFixture<ParcelFinderComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        ParcelFinderComponent, 
        TranslateModule.forRoot({
          loader: { provide: TranslateLoader, useClass: MockTranslateLoader },
        }),
      ],
      providers: [
        provideHttpClient(), 
        provideHttpClientTesting()
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ParcelFinderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
