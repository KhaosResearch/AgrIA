import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ParcelCadastralComponent } from './parcel-cadastral.component';

describe('ParcelCadastralComponent', () => {
  let component: ParcelCadastralComponent;
  let fixture: ComponentFixture<ParcelCadastralComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ParcelCadastralComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ParcelCadastralComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
