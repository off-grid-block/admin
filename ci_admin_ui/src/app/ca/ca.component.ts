import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-ca',
  templateUrl: './ca.component.html',
  styleUrls: ['./ca.component.css']
})
export class CaComponent implements OnInit {
  public selected;
  constructor() { }

  ngOnInit() {
    this.selected=0;
  }
  
  select(select) {
    this.selected=select;
  }
}
