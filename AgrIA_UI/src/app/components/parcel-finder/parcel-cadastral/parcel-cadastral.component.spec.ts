import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ParcelCadastralComponent } from './parcel-cadastral.component';

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

describe('ParcelCadastralComponent', () => {
  let component: ParcelCadastralComponent;
  let fixture: ComponentFixture<ParcelCadastralComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        ParcelCadastralComponent, 
        TranslateModule.forRoot({
          loader: { provide: TranslateLoader, useClass: MockTranslateLoader },
        }),
      ],
      providers: [
        provideHttpClient(), 
        provideHttpClientTesting()
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ParcelCadastralComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
