import { Component, EventEmitter, inject, Input, Output, signal, WritableSignal } from '@angular/core';
import { TranslateModule } from '@ngx-translate/core';
import { FormsModule } from '@angular/forms';
import { IFindParcelresponse } from '../../../models/parcel-finder.model';
import { NotificationService } from '../../../services/notification.service/notification.service';
import { ISigpacLocationData } from '../../../models/parcel-locator.model';
import { ParcelFinderService } from '../../../services/parcel-finder.service/parcel-finder.service';
import { NgSelectModule } from '@ng-select/ng-select';

@Component({
  selector: 'app-parcel-locator',
  imports: [TranslateModule, FormsModule, NgSelectModule],
  templateUrl: './parcel-locator.component.html',
  styleUrl: './parcel-locator.component.css',
})
export class ParcelLocatorComponent {
  // Loading flag
  @Input() isLoading: WritableSignal<boolean> = signal(false);

  // Parcel found emmiter
  @Output() parcelFound = new EventEmitter<IFindParcelresponse>();
  // Start loading process emmiter
  @Output() loadingStarted = new EventEmitter<number>();
  // Find parcel request emmiter
  @Output() findParcelRequest = new EventEmitter<FormData>();

  // Id and province att
  protected province: string | null = null;
  // Id and municipality att
  protected municipality: string | null = null;
  // Polygon id att
  protected polygon: number | null = null;
  // Parcel Id att
  protected parcelId: number | null = null;

  // List of all municipalities associated to each province
  protected sigpacLocationData: ISigpacLocationData[] = [];
  // List of all provinces for dropdown display
  protected provinces: string[] = [];
  // List of all municipalities for dropdown display
  protected municipalities: string[] = [];

  // Max date field value
  protected today: string = new Date().toISOString().split('T')[0];
  // Selected date field value
  protected selectedDate: string = this.today;

  // Valid input flag
  protected isValidInput: WritableSignal<boolean> = signal(true);
  // Estimated loading duration value (in seconds)
  protected maxLoadingDuration: number = 60;

  // Parcel Finder service
  private parcelFinderService: ParcelFinderService = inject(ParcelFinderService);
  // Notification service
  private notificationService: NotificationService = inject(NotificationService);

  ngOnInit() {
    this.loadSigpacLocationData();
  }

  /**
   * Loads SIGPAC province and municipalities data.
   */
  private loadSigpacLocationData() {
    this.parcelFinderService.loadSigpacLocationData().subscribe(
      (sigpacLocationData: ISigpacLocationData[]) => {
        this.sigpacLocationData = sigpacLocationData;
        this.provinces = this.sigpacLocationData.map(data => data.province);
      },
      error => {
        this.notificationService.showNotification(
          'parcel-finder.sigpac-table.error',
          `\n${error.error.error}`,
          'error',
          10000
        );
        console.error('Error loading crop classifications:', error);
      }
    );
  }

  /**
   * Handles changes when selecting a province.
   * @param selected - Province entry
   */
  protected onProvinceChange(selected: string) {
    this.municipalities = this.getMunicipalities(selected);
    this.municipality = ''; // reset previous selection
  }

  /**
   * Updates dropdown municipalities based on selected province.
   *
   * @param province - Province entry
   * @returns
   */
  private getMunicipalities(province: string): string[] {
    const entry = this.sigpacLocationData.find(data => data.province === province);
    return entry ? entry.municipalities : [];
  }

  /**
   * Prevents user from typing anything other than integers
   *
   * @param event
   * @returns
   */
  public restrictKeys(event: KeyboardEvent) {
    const allowedKeys = ['Backspace', 'Tab', 'ArrowLeft', 'ArrowRight'];

    // Always allow navigation and deletion
    if (allowedKeys.includes(event.key)) return;

    // Allow digits 0–9
    if (/^[0-9]$/.test(event.key)) return;

    // Block everything else (e, -, ., +, letters…)
    event.preventDefault();
  }

  /**
   * Limits input digits length for input field
   *
   * @param event
   * @param length
   * @param elementId
   */
  public limitLength(event: any, length: number) {
    let value = event.target.value;
    if (value.length > length) {
      value = value.slice(0, length);
      // Update values
      event.target.value = value;
      if (length === 3) {
        this.polygon = value;
      } else {
        this.parcelId = value;
      }
    }
  }

  /**
   * Padds the input with 0s when input value length is not full
   *
   * @param event
   * @param length
   */
  public formatInput(event: any, length: number) {
    let value = event.target.value;
    if (value.length < length && value !== '') {
      value = value.padStart(length, '0');
    }
    // Update values
    event.target.value = value;
    if (length === 3) {
      this.polygon = value;
    } else {
      this.parcelId = value;
    }
  }

  /**
   * Validates input before sending a request.
   */
  private validateInput() {
    this.isValidInput.set(false);
    if (!this.province || this.province.length < 1) {
      const message = 'Province not specified.';
      this.notificationService.showNotification('parcel-locator.missing.province', '', 'error', 10000);
      throw new Error(message);
    } else if (!this.municipality || this.municipality.length < 1) {
      const message = 'Municipality not specified.';
      this.notificationService.showNotification('parcel-locator.missing.municipality', '', 'error', 10000);
      throw new Error(message);
    } else if (!this.polygon) {
      const message = 'Polygon not specified.';
      this.notificationService.showNotification('parcel-locator.missing.polygon', '', 'error', 10000);
      throw new Error(message);
    } else if (!this.parcelId) {
      const message = 'Parcel not specified.';
      this.notificationService.showNotification('parcel-locator.missing.parcel-id', '', 'error', 10000);
      throw new Error(message);
    }
    this.isValidInput.set(true);
  }

  /**
   * Builds request and send parcel request to parent component.
   */
  protected findParcel() {
    try {
      // Validate input before sending request
      this.validateInput();

      if (this.isValidInput()) {
        // Init loading notifications
        this.notificationService.showNotification('parcel-finder.searching', '', 'info');
        this.isLoading.set(true);
        this.loadingStarted.emit(this.maxLoadingDuration);
        document.body.style.cursor = 'progress';

        // Create find parcel request
        const formData = new FormData();
        formData.append('province', this.province!!);
        formData.append('municipality', this.municipality!!);
        formData.append('polygon', String(this.polygon!!));
        formData.append('parcelId', String(this.parcelId!!));
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
   * Resets form values
   */
  protected clearForm() {
    this.province = '';
    this.municipality = '';
    this.polygon = null;
    this.parcelId = null;
    this.selectedDate = this.today;
  }
}
