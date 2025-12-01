import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ParcelDrawerComponent } from './parcel-drawer.component';

describe('ParcelDrawerComponent', () => {
  let component: ParcelDrawerComponent;
  let fixture: ComponentFixture<ParcelDrawerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ParcelDrawerComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ParcelDrawerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
