import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import{ HttpClientModule } from '@angular/common/http';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { CaComponent } from './ca/ca.component';
import { FormsModule } from '@angular/forms';
import { NgxQRCodeModule } from 'ngx-qrcode2';
import { InvitationComponent } from './invitation/invitation.component';
import { SchemaComponent } from './schema/schema.component';
import { CredentialComponent } from './credential/credential.component';

@NgModule({
  declarations: [
    AppComponent,
    CaComponent,
    InvitationComponent,
    SchemaComponent,
    CredentialComponent,
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule,
    FormsModule,
    NgxQRCodeModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
