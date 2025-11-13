import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { map, Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { IChatParcelResponse } from '../../models/chat.model';

@Injectable({
  providedIn: 'root'
})
export class ChatService {

  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  public loadParcelDataToChat(request:FormData): Observable<IChatParcelResponse> {
    return this.http.post<{ response: IChatParcelResponse }>(`${this.apiUrl}/load-parcel-data-to-chat`, request)
    .pipe(map(res => res.response));
  }

  public loadInputSuggestion(request: FormData): Observable<string> {
    return this.http.post<{ response: string }>(`${this.apiUrl}/get-input-suggestion`, request)
    .pipe(map(res => res.response));
  }
}
