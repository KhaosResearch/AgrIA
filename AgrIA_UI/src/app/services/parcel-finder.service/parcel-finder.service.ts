import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, map, Observable } from 'rxjs';
import { ICropClassification } from '../../models/parcel-drawer.model';
import { environment } from '../../../environments/environment';
import { IFindParcelResponse } from '../../models/parcel-finder.model';
import { ISigpacLocationData } from '../../models/parcel-locator.model';
import { CROP_CLASSIFICATION_FILENAME } from '../../config/constants';

@Injectable({
  providedIn: 'root',
})
export class ParcelFinderService {
  private apiUrl = environment.apiUrl;
  private parcelInfoSubject = new BehaviorSubject<IFindParcelResponse | null>(null);
  parcelInfo$ = this.parcelInfoSubject.asObservable();

  constructor(private http: HttpClient) {}

  loadParcelDescription(request: FormData): Observable<string> {
    return this.http
      .post<{ response: string }>(`${this.apiUrl}/load-parcel-description`, request)
      .pipe(map(res => res.response));
  }

  findParcel(request: FormData): Observable<IFindParcelResponse> {
    return this.http
      .post<{ response: IFindParcelResponse }>(`${this.apiUrl}/find-parcel`, request)
      .pipe(map(res => res.response));
  }

  loadSigpacLocationData(): Observable<ISigpacLocationData[]> {
    return this.http.get<ISigpacLocationData[]>('data/sigpac_location_data.json');
  }

  loadCropClassifications(lang: String): Observable<ICropClassification[]> {
    return this.http.get<ICropClassification[]>(CROP_CLASSIFICATION_FILENAME + lang + '.json');
  }

  isCoordInZone(request: FormData): Observable<boolean> {
    return this.http.post<{ response: boolean }>(`${this.apiUrl}/is-coord-in-zone`, request).pipe(map(res => res.response));
  }

  setParcelInfo(data: IFindParcelResponse) {
    this.parcelInfoSubject.next(data);
  }
}
