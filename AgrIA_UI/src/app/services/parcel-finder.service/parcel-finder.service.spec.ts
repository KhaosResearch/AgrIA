import { TestBed } from '@angular/core/testing';

import { ParcelFinderService } from './parcel-finder.service';

describe('ParcelFinderService', () => {
  let service: ParcelFinderService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ParcelFinderService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
