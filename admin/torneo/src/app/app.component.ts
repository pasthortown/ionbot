import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { BackendService } from './services/backend.service';
import { NgxSpinnerService } from 'ngx-spinner';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})

export class AppComponent implements OnInit {
  torneo: any =  null;
  id_torneo: number = 0;

  constructor(private route: ActivatedRoute, private backendService: BackendService, private spinner: NgxSpinnerService) {}

  ngOnInit() {
    this.route.queryParams.subscribe(params => {
      this.id_torneo = params['id_torneo'] || 0;
      if (this.id_torneo != 0) {
        this.get_data_torneo();
      }
    });
  }

  get_data_torneo() {
    this.spinner.show();
    this.backendService.detalle_torneo('depositos', 'torneos', this.id_torneo.toString()).then( (r: any) => {
      this.spinner.hide();
      this.torneo = r.response.torneo;
      console.log(this.torneo);
    }).catch( e => {console.log(e); this.spinner.hide();} );
  }
}
