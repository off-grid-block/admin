import { Component, OnInit } from '@angular/core';
import { Service1Service } from '../service1.service';
@Component({
  selector: 'app-schema',
  templateUrl: './schema.component.html',
  styleUrls: ['./schema.component.css']
})
export class SchemaComponent implements OnInit {
  public schema_name;
  public attributes;
  public schema_id=null;
  public cred_def_id=null;

  constructor(private service1 : Service1Service) { }

  ngOnInit() {

  }

  createSchemaCredDef() {
    let data = {
      "schema_name" : this.schema_name,
      "attributes" : this.attributes,
    }

    this.service1.createSchemaCredDef(data).subscribe((res:any)=>{
      alert("Schema and credential definition created")
      this.schema_id=res["schema_id"]
      this.cred_def_id=res["credential_definition_id"]
    });
  }
}
