import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ParcelDisplayComponent } from './parcel-display.component';

describe('ParcelDisplayComponent', () => {
  let component: ParcelDisplayComponent;
  let fixture: ComponentFixture<ParcelDisplayComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ParcelDisplayComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ParcelDisplayComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
