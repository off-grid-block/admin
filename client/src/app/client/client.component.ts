import { Component, OnInit } from '@angular/core';
import { ClientServiceService } from '../client-service.service';

@Component({
  selector: 'app-client',
  templateUrl: './client.component.html',
  styleUrls: ['./client.component.css']
})

export class ClientComponent implements OnInit {
  public client_name : string;
  public client_port : Number;
  public invitation : any;
  public connectionList : any=[];
  public message : string;
  public conn_id : number;

  constructor(private clientService : ClientServiceService) {
    this.client_port=8008;
   }

  getConnections() {
    this.clientService.handle_get_connections().subscribe((res:any)=>{
      this.connectionList=res['connectionList'];
    });
  }

  ngOnInit() {
    this.getConnections();
    // This is a function for getting the name of the Agent
    this.clientService.handle_get_client_name().subscribe((res:any)=>{
      this.client_name=res['client_name'];
    });
  }

  // This is a function for inputing invitation
  getInvitation() {
    if(this.invitation!="" && this.invitation!=null) {
      let data={
        "invitation"  : {"invitation" : this.invitation},
      }
      this.clientService.handle_input_invitation(data).subscribe((res:any)=>{
        if(res['status']==true) {
          alert("connected!!");
          this.getConnections();
        }
      });
    } else {
      alert("Invitation is empty")
    }
  }  

  getInvitationFromMsp() {
    let data : {};
    this.clientService.getInvitationFromMsp().subscribe((res:any)=>{
      data={
        "port"        : this.client_port,
        "invitation"  : {"invitation" : res},
      }
      this.clientService.handle_input_invitation(data).subscribe((res:any)=>{
        if(res['status']==true) {
          alert("connected!!");
          this.getConnections();
        }
      });
    });
  }

  getInvitationFromIssuer() {
    let data : {};
    this.clientService.getInvitationFromIssuer().subscribe((res:any)=>{
      data={
        "port"        : this.client_port,
        "invitation"  : {"invitation" : res},
      }
      this.clientService.handle_input_invitation(data).subscribe((res:any)=>{
        if(res['status']==true) {
          alert("connected!!");
          this.getConnections();
        }
      });
    });  
  }
}
