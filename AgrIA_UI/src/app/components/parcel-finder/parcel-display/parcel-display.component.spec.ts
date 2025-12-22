import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ParcelDisplayComponent } from './parcel-display.component';

import { provideHttpClient } from '@angular/common/http';

import { provideHttpClientTesting } from '@angular/common/http/testing';

import { TranslateModule, TranslateLoader } from '@ngx-translate/core';

import { Observable, of } from 'rxjs';

/*
 * Init the TranslateModule with TranslateLoader to empty
 */
export class MockTranslateLoader implements TranslateLoader {
  getTranslation(lang: string): Observable<any> {
    return of({});
  }
}
describe('ParcelDisplayComponent', () => {
  let component: ParcelDisplayComponent;
  let fixture: ComponentFixture<ParcelDisplayComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        ParcelDisplayComponent, 
        TranslateModule.forRoot({
          loader: { provide: TranslateLoader, useClass: MockTranslateLoader },
        }),
      ],
      providers: [
        provideHttpClient(), 
        provideHttpClientTesting()
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ParcelDisplayComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
