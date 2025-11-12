import { Component, inject, signal, WritableSignal } from '@angular/core';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { ParcelCadastralComponent } from './parcel-cadastral/parcel-cadastral.component';
import { ParcelDisplayComponent } from "./parcel-display/parcel-display.component";
import { ParcelDrawerComponent } from "./parcel-drawer/parcel-drawer.component";
import { ParcelLocatorComponent } from './parcel-locator/parcel-locator.component';
import { IFindParcelresponse } from '../../models/parcel-finder.model';
import { ParcelFinderService } from '../../services/parcel-finder.service/parcel-finder.service';
import { NotificationService } from '../../services/notification.service/notification.service';

@Component({
  selector: 'app-parcel-finder',
  imports: [
    TranslateModule,
    ParcelCadastralComponent,
    ParcelDisplayComponent,
    ParcelDrawerComponent,
    ParcelLocatorComponent,
],
  templateUrl: './parcel-finder.component.html',
  styleUrl: './parcel-finder.component.css'
})
export class ParcelFinderComponent {
  // Active tab attribute
  protected activeTab: 'finder' | 'drawer' | 'locator' = 'finder';
  private selectedParcelInfo: IFindParcelresponse | null = null;
  protected isLoading: WritableSignal<boolean> = signal(false);
  protected maxLoadingDuration = 40;

  private parcelFinderService: ParcelFinderService = inject(ParcelFinderService);
  private notificationService: NotificationService = inject(NotificationService);
  private translateService: TranslateService = inject(TranslateService);

  constructor() {}

  protected handleParcelFound(parcel: IFindParcelresponse) {
    this.selectedParcelInfo = parcel;
    this.isLoading.set(false);
  }

  protected handleLoadingStarted(duration: number) {
    this.isLoading.set(true);
    this.maxLoadingDuration = duration;
  }

  protected handleLoadingFinished() {
    this.isLoading.set(false);
  }

  protected handleError(error: any) {
    console.error('Parcel fetch error:', error);
    this.isLoading.set(false);
  }

  protected handleFindParcelRequest(request: FormData) {
    this.scrollToDisplay();
    this.parcelFinderService.findParcel(request).subscribe({
      next: (response: IFindParcelresponse) => {
        // Finish loading
        this.notificationService.showNotification("parcel-finder.success","","success")
        document.body.style.cursor = 'default';
        this.isLoading.set(false);
        // Get parcel info
        this.selectedParcelInfo = response;
        this.parcelFinderService.setParcelInfo(this.selectedParcelInfo);
        console.log("Parcel finder response:", response)
      },
      error: (err) => {
        const errorMessage = err.error.error.includes("No images are available")? 
          this.translateService.currentLang === "es"? "No hay imágenes disponibles para la fecha seleccionada, las imágenes se procesan al final de cada mes."
            : "No images are available for the selected date, images are processed at the end of each month."
          : err.error.error
        this.notificationService.showNotification("parcel-finder.error",`\n${errorMessage}`,"error", 10000)
        console.error('Parcel fetch failed', err);
        // Finish loading
        document.body.style.cursor = 'default';
        this.isLoading.set(false);
      },
      complete: () => {
        // Finish loading
        document.body.style.cursor = 'default';
        this.isLoading.set(false);
        document.body.style.cursor = 'default';
      }
    });

  }

  protected handleLocatorFindParcelRequest(request: FormData) {
    this.scrollToDisplay();
    console.log("request", request);
  }

  /**
   * Scrolls view to map element.
   */
  private scrollToDisplay(): void {
    const mapElement = document.getElementById('display');
    if (mapElement) {
      mapElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

}
