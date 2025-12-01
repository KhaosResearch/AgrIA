import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ParcelLocatorComponent } from './parcel-locator.component';

describe('ParcelLocatorComponent', () => {
  let component: ParcelLocatorComponent;
  let fixture: ComponentFixture<ParcelLocatorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ParcelLocatorComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ParcelLocatorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
