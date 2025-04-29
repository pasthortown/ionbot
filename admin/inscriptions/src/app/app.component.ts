import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { NgxFileDropEntry } from 'ngx-file-drop';
import { BackendService } from './services/backend.service';
import Swal from 'sweetalert2';
import { NgxSpinnerService } from 'ngx-spinner';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  usuario_discord: string = "";
  id_discord: string = "";
  id_torneo: string = "";
  fullname: string = "";
  telefono_celular: string = "";
  correo_electronico: string = "";
  validate_file_size: boolean = true;
  validate_file_type: boolean = true;
  inscrito: boolean = false;
  valor_deposito: number = 0;
  file: any = null;
  guardando: boolean = false;
  value_tornaument: number = 0;
  saldo: number = 0 ;
  torneo: any = {};

  constructor(private route: ActivatedRoute, private backendService: BackendService, private spinner: NgxSpinnerService) {}

  ngOnInit() {
    this.route.queryParams.subscribe(params => {
      const token = params['token'];
      const decodedToken = this.decode_jwt(token);
      this.usuario_discord = decodedToken.usuario_discord || "";
      this.id_discord = decodedToken.id_discord || "";
      this.id_torneo = decodedToken.id_torneo || "";
      if (this.id_discord != "") {
        this.get_saldo();
      }
      if (this.id_torneo != "") {
        this.get_valor_torneo();
      }
    });
  }

  decode_jwt(token: string) {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(window.atob(base64));
  }
  formatFileSize(size: number): string {
    if (size >= 1024 * 1024) {
      return (size / (1024 * 1024)).toFixed(2) + ' MB';
    } else {
      return (size / 1024).toFixed(2) + ' KB';
    }
  }

  dropped(files: NgxFileDropEntry[]) {
    this.validate_file_size = true;
    for (const droppedFile of files) {
      if (droppedFile.fileEntry.isFile) {
        const fileEntry = droppedFile.fileEntry as FileSystemFileEntry;
        fileEntry.file((file: File) => {
          const reader = new FileReader();
          reader.readAsDataURL(file);
          reader.onload = () => {
            if (reader.result != null) {
              if (file.type.toString().search('image') != -1) {
                this.validate_file_type = true;
                let new_file = {
                  name: file.name,
                  type: file.type,
                  size: file.size,
                  size_show: this.formatFileSize(file.size),
                  file_base64: reader.result.toString().split(',')[1],
                };
                if (file.size > (10 * 1024 * 1024)) {
                  this.validate_file_size = false;
                }
                this.file = new_file;
              } else {
                this.validate_file_type = false;
              }
            }
          };
        });
      }
    }
  }

  get_saldo() {
    this.backendService.get_saldo('depositos', this.id_discord).then( (r: any) => {
      this.saldo = Number.parseFloat(r.response);
    }).catch( e => console.log(e) );
  }

  get_valor_torneo() {
    let output_model: any = {
      "id": 1,
      "costo": 1,
      "fecha": 1,
      "pais": 1,
      "juego": 1,
      "plataforma": 1
    };
    this.backendService.search_items('torneos', 'id_torneo', this.id_torneo, output_model).then( (r: any) => {
      this.torneo = r.response[0];
      this.value_tornaument = Number.parseFloat(this.torneo.costo);
    }).catch( e => console.log(e) );
  }

  enviar_solicitud() {
    this.guardando = true;
    this.spinner.show();
    if (this.file == null) {
      let data = {
        usuario_discord: this.usuario_discord,
        id_discord: this.id_discord,
        id_torneo: this.id_torneo,
        fullname: this.fullname,
        telefono_celular: this.telefono_celular,
        correo_electronico: this.correo_electronico,
        valor_deposito: this.valor_deposito,
        aprobado: false,
        file_id: '',
        costo_evento: this.value_tornaument,
        saldo_anterior: this.saldo,
        saldo_actual: this.saldo + this.valor_deposito - this.value_tornaument
      }
      this.backendService.upload_items('depositos', [data]).then( (r: any) => {
        this.spinner.hide();
        Swal.fire({
          title: 'Solicitud de Inscripción',
          text: 'Hemos recibido tu solicitud, en la brevedad posible te daremos una respuesta',
          icon: 'success'
        }).then( resp => {
          this.guardando = false;
          this.fullname = "";
          this.telefono_celular = "";
          this.correo_electronico = "";
          this.valor_deposito = 0;
          this.file = null;
          this.inscrito = true;
        });
      }).catch( e => {console.log(e); this.guardando = false; this.spinner.hide();} );
    } else {
      this.backendService.upload_items('archivos', [this.file]).then( (r_file: any) => {
        let file_id: string = r_file.response[0].item_id;
        let data = {
          usuario_discord: this.usuario_discord,
          id_discord: this.id_discord,
          id_torneo: this.id_torneo,
          fullname: this.fullname,
          telefono_celular: this.telefono_celular,
          correo_electronico: this.correo_electronico,
          valor_deposito: this.valor_deposito,
          aprobado: false,
          file_id: file_id,
          costo_evento: this.value_tornaument,
          saldo_anterior: this.saldo,
          saldo_actual: this.saldo + this.valor_deposito - this.value_tornaument
        }
        this.backendService.upload_items('depositos', [data]).then( (r: any) => {
          this.spinner.hide();
          Swal.fire({
            title: 'Solicitud de Inscripción',
            text: 'Hemos recibido tu solicitud, en la brevedad posible te daremos una respuesta',
            icon: 'success'
          }).then( resp => {
            this.guardando = false;
            this.fullname = "";
            this.telefono_celular = "";
            this.correo_electronico = "";
            this.valor_deposito = 0;
            this.file = null;
            this.inscrito = true;
          });
        }).catch( e => {console.log(e); this.guardando = false; this.spinner.hide();} );
      }).catch( e => {console.log(e); this.guardando = false; this.spinner.hide();} );
    }
  }
}
