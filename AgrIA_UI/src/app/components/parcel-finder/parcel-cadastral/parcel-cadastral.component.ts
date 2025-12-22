import { Component, EventEmitter, inject, Input, Output, signal, WritableSignal } from '@angular/core';
import { IFindParcelresponse } from '../../../models/parcel-finder.model';
import { FormsModule } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';
import { NotificationService } from '../../../services/notification.service/notification.service';

@Component({
  selector: 'app-parcel-cadastral',
  imports: [FormsModule, TranslateModule],
  templateUrl: './parcel-cadastral.component.html',
  styleUrl: './parcel-cadastral.component.css',
})
export class ParcelCadastralComponent {
  // Loading variable for styling
  @Input() isLoading: WritableSignal<boolean> = signal(false);

  // Parcel found emmiter
  @Output() parcelFound = new EventEmitter<IFindParcelresponse>();
  // Start loading process emmiter
  @Output() loadingStarted = new EventEmitter<number>();
  // Find parcel request emmiter
  @Output() findParcelRequest = new EventEmitter<FormData>();

  // Cadastral reference of the parcel
  public cadastralReference: string = '14048A001001990000RM'; // TODO: REMOVE WHEN TESTING IS DONE
  // Date for which the parcel image is requested
  public selectedDate: string = new Date().toISOString().split('T')[0];
  // Max date allowed for the date picker
  public today: string = new Date().toISOString().split('T')[0];
  // Valid input flag:
  private isValidInput: WritableSignal<boolean> = signal(true);
  // Maximum seconds set for the progress bar
  public maxLoadingDuration: number = 40;
  // Selected parcel information
  protected selectedParcelInfo: IFindParcelresponse | null = null;
  // URL of the parcel's satellite image
  public parcelImageUrl: string | null = null;

  // Service for notifications
  private notificationService = inject(NotificationService);

  constructor() {}

  /**
   * Finds a parcel based on the provided cadastral reference and selected date.
   *
   */
  public findParcel() {
    try {
      // Validate input
      this.validateInput();

      if (this.isValidInput()) {
        // Init loading notifications
        this.notificationService.showNotification('parcel-finder.searching', '', 'info');
        this.isLoading.set(true);
        this.loadingStarted.emit(this.maxLoadingDuration);
        document.body.style.cursor = 'progress';

        // Reset parcel image
        this.parcelImageUrl = null;

        // Create find parcel request
        const formData = new FormData();
        formData.append('cadastralReference', this.cadastralReference);
        formData.append('selectedDate', this.selectedDate);
        formData.append('isFromCadastralReference', 'True');

        // Output request to parcel finder component
        this.findParcelRequest.emit(formData);
      }
    } catch (err) {
      if (this.isValidInput()) {
        this.notificationService.showNotification('parcel-finder.error', `\n${err}`, 'error', 10000);
      }
      console.error('Request error:', err);
    }
  }

  /**
   * Validate input before sending request
   */
  private validateInput() {
    this.isValidInput.set(false);
    if (!this.cadastralReference || this.cadastralReference.length !== 20) {
      const message = 'Municipality not specified.';
      this.notificationService.showNotification('parcel-cadastral.missing.cadastral', '', 'error', 10000);
    }

    this.isValidInput.set(true);
  }

  /**
   * Clears all form info
   */
  public clearForm() {
    this.cadastralReference = '';
    this.selectedDate = new Date().toISOString().split('T')[0];
  }
}
