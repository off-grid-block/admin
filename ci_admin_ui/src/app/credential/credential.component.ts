import { Component, OnInit } from '@angular/core';
import { Service1Service } from '../service1.service';

@Component({
  selector: 'app-credential',
  templateUrl: './credential.component.html',
  styleUrls: ['./credential.component.css']
})
export class CredentialComponent implements OnInit {
  public custom={};
  public credential_definition_id=null;
  public attributes=[];
  public offerSent=false;
  public credentialIssued=null;
  public connection_id = null;
  public credDefList=[]
  public connectionList=[]
  public connCredDefSelect=false;

  constructor(private service1 : Service1Service) { 
  
  }

  ngOnInit() {
    this.service1.get_cred_def_list().subscribe((res:any)=>{
      this.credDefList=res['credDefIdList']
      this.service1.get_connection_list().subscribe((res:any)=>{
        this.connectionList=res['connectionList']
        console.log(this.connectionList)
      });
    });
  }

  sendCredentialOffer() {
    let data = {
      credential_definition_id : this.credential_definition_id,
      attr_data : this.custom,
      connection_id : this.connection_id,
    }

    this.service1.sendCredentialOffer(data).subscribe((res:any)=>{
      if(res["status"] == true){
        this.offerSent=true;
      }
    });
  }

  issueCredential() {
    this.service1.issueCredential().subscribe((res:any)=>{
      if(res["status"] == true){
        this.credentialIssued="Credential has been issued!!"
      }
    });
  }

  connCredDefSelected() {
    if(this.credential_definition_id==null || this.credential_definition_id==''
    || this.connection_id==null || this.connection_id==''){
      this.connCredDefSelect = false
      return
    }

    this.connCredDefSelect = true
    this.offerSent = false
    var itm;
    for(itm=0; itm<this.credDefList.length;itm++) {
      if(this.credDefList[itm]['credential_definition_id']==this.credential_definition_id) {
        this.attributes=this.credDefList[itm]['attr_list']
      }
    }

    for(itm=0; itm<this.attributes.length;itm++) {
      this.custom[this.attributes[itm]]=null;
    }
  }
}
