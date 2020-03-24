import { Injectable } from '@angular/core';
import{HttpClient} from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class ClientServiceService {
  public url;
  public ip="http://10.53.17.40:8008"
  public ip2='';
  constructor(private http : HttpClient) { 

  }

  handle_get_client_name() {
    this.url = this.ip+"/get_client_name";
    return this.http.get(this.url); 
  }

  handle_input_invitation(data) {
    this.url = this.ip+"/input_invitation";
    return this.http.post(this.url, data.invitation);
  }

  handle_get_connections() {
    this.url = this.ip+"/get_connections";
    return this.http.get(this.url); 
  }

  getInvitationFromMsp() {
    this.ip2="http://10.53.17.40:8003"
    this.url = this.ip2+"/create_invitation"
    return this.http.get(this.url); 
  }

  getInvitationFromIssuer() {
    this.ip2="http://10.53.17.40:8003"
    this.url = this.ip2+"/create_invitation"
    return this.http.get(this.url); 
  }
}
