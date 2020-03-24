import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { CaComponent } from './ca/ca.component';
import { InvitationComponent } from './invitation/invitation.component';
import { SchemaComponent } from './schema/schema.component';
import { CredentialComponent } from './credential/credential.component'

const routes: Routes = [
  {path:'',component:CaComponent, children :[
    {path:'',component:InvitationComponent},
    {path:'schema',component:SchemaComponent},
    {path:'credential',component:CredentialComponent},
  ]},
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
