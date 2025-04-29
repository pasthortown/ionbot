import { Component, OnInit } from '@angular/core';
import { BackendService } from './services/backend.service';
import { NgxSpinnerService } from 'ngx-spinner';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})

export class AppComponent implements OnInit{

  depositos: any[] = [];
  deposito_file: any = null;
  deposito_selected: any = null;

  constructor( private backendService: BackendService, private spinner: NgxSpinnerService, private modalService: NgbModal) {}

  ngOnInit(): void {
    this.refresh();
  }

  refresh() {
    this.get_depositos();
  }

  get_depositos() {
    this.spinner.show();
    this.depositos = [];
    let torneos: any[] = [];
    let output_model_torneos = {
      id_torneo: 1,
      fecha: 1,
      pais: 1,
      juego: 1,
      plataforma: 1,
      costo: 1
    }
    this.backendService.get_items('torneos', output_model_torneos).then( (r_torneos: any) => {
      torneos = r_torneos.response;
      let output_model = {
        usuario_discord: 1,
        id_discord: 1,
        id_torneo: 1,
        fullname: 1,
        telefono_celular: 1,
        correo_electronico: 1,
        valor_deposito: 1,
        aprobado: 1,
        file_id: 1,
        costo_evento: 1
      };
      this.backendService.get_items('depositos', output_model).then( (r: any) => {
        this.spinner.hide();
        this.depositos = r.response;
        this.depositos.forEach( (deposito: any) => {
          torneos.forEach( (torneo: any) => {
            if (deposito.id_torneo == torneo.id_torneo) {
              deposito.torneo = torneo
            }
          });
        });
      }).catch( e => console.log(e) );
    }).catch( e => console.log(e) );
  }

  show_modal_usuario(deposito: any, modal_content: any) {
    this.spinner.show();
    this.backendService.get_saldo('depositos', deposito.id_discord).then( (r: any) => {
      this.deposito_selected = deposito;
      this.deposito_selected.saldo = Number.parseFloat(r.response);
      this.spinner.hide();
      this.modalService.open(modal_content);
    }).catch( e => console.log(e) );
  }

  get_deposito_file(file_id: string, modal_content: any) {
    this.spinner.show();
    let output_model = {
      name: 1,
      type: 1,
      size: 1,
      size_show: 1,
      file_base64: 1
    };
    this.backendService.get_item('archivos', file_id, output_model).then( (r: any) => {
      this.deposito_file = r.response;
      this.spinner.hide();
      this.modalService.open(modal_content);
      console.log(this.deposito_file);
    }).catch( e => console.log(e) );
  }

  aprobar(deposito: any) {
    deposito.aprobado = true;
    this.backendService.update_item('depositos', deposito.item_id, deposito).then( (r: any) => {
      this.refresh();
    }).catch( e => console.log(e) );
  }

  rechazar(deposito: any) {
    deposito.aprobado = false;
    this.backendService.update_item('depositos', deposito.item_id, deposito).then( (r: any) => {
      this.refresh();
    }).catch( e => console.log(e) );
  }
}
