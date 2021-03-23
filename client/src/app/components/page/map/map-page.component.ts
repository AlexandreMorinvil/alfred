import { Component, OnInit } from "@angular/core";
import { MapCatalogService } from "@app/service/map-catalog/map-catalog.service";

@Component({
  selector: "app-map-page",
  templateUrl: "./map-page.component.html",
  styleUrls: ["./map-page.component.scss", "../page.component.scss"],
})
export class MapPageComponent implements OnInit{
  constructor(public mapCatalogService : MapCatalogService){

  }
  ngOnInit(){
    this.mapCatalogService.reloadMap();
  }

}
