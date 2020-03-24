import { Component, OnInit } from '@angular/core';
import { Service1Service } from '../service1.service';

@Component({
  selector: 'app-invitation',
  templateUrl: './invitation.component.html',
  styleUrls: ['./invitation.component.css']
})
export class InvitationComponent implements OnInit {
  public invitation=null
  constructor(private service1 : Service1Service) { }

  ngOnInit() {
  }

  createInvitation() {
    this.service1.createInvitation().subscribe((res:any)=>{
      this.invitation=JSON.stringify(res);
    });
  }

}
