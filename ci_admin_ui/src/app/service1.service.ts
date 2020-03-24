import { Injectable } from '@angular/core';
import{HttpClient} from '@angular/common/http';
import { Options } from 'selenium-webdriver/opera';

@Injectable({
  providedIn: 'root'
})
export class Service1Service {
  public url;
  public ip="http://10.53.17.40:8003";
  constructor(private http : HttpClient) {

  }

  createInvitation() {
    this.url = this.ip+"/create_invitation";
    return  this.http.get(this.url);
  }

  createSchemaCredDef(data) {
    this.url = this.ip+"/create_schema_cred_def";
    return this.http.post(this.url, data);
  }

  sendCredentialOffer(data) {
    this.url = this.ip+"/send_credential_offer";
    return this.http.post(this.url, data);
  }
  

  issueCredential() {
    this.url = this.ip+"/issue_credential";
    return  this.http.get(this.url);
  }

  get_cred_def_list() {
    this.url = this.ip+"/get_cred_def_list";
    return  this.http.get(this.url);  
  }

  get_connection_list() {
    this.url = this.ip+"/get_connection_list";
    return  this.http.get(this.url); 
  }
}
