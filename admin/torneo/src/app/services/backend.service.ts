import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { HttpHeaders } from '@angular/common/http';
import { environment } from './../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class BackendService {

  options: any = {};
  api_catalog: string = environment.api_backend_url;

  constructor(private http: HttpClient) {
    let headers: HttpHeaders = new HttpHeaders().set('Content-Type', 'application/json');
    this.options = {headers: headers};
  }

  detalle_torneo(catalog: string, catalog_torneo: string, id_torneo: string): Promise<any> {
    const data = {catalog_torneo: catalog_torneo, id_torneo: id_torneo};
    return this.http.post(this.api_catalog + catalog +'/detalle_torneo', JSON.stringify(data), this.options).toPromise();
  }
}
