import { ChangeDetectorRef, Component, inject, Input, signal, WritableSignal } from '@angular/core';
import { ParcelFinderService } from '../../../services/parcel-finder.service/parcel-finder.service';
import { IFindParcelresponse } from '../../../models/parcel-finder.model';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';
import { ProgressBarComponent } from '../../progress-bar/progress-bar.component';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-parcel-display',
  imports: [FormsModule, TranslateModule, ProgressBarComponent],
  templateUrl: './parcel-display.component.html',
  styleUrl: './parcel-display.component.css',
})
export class ParcelDisplayComponent {
  // Loading image flag
  @Input() public isLoading: WritableSignal<boolean> = signal(false);
  // Planned duration of the loading
  @Input() public maxLoadingDuration: number = 40;
  // URL of the parcel's satellite image
  protected parcelImageUrl: string | null | undefined = null;
  // Selected parcel information
  private selectedParcelInfo: IFindParcelresponse | null = null;
  // User preference for longer image description
  protected isDetailedDescription: boolean = false;

  // Service to communicate parcel info from parcel finder to chat
  private parcelFinderService = inject(ParcelFinderService);
  // Router for navigation
  private router: Router = inject(Router);
  // Subscriptions service
  private subscription = new Subscription();
  // Change detection service
  private cdRef: ChangeDetectorRef = inject(ChangeDetectorRef);

  constructor() {}

  ngOnInit(): void {
    this.subscription = this.parcelFinderService.parcelInfo$.subscribe(parcelInfo => {
      if (parcelInfo) {
        this.selectedParcelInfo = parcelInfo;
        this.parcelImageUrl = parcelInfo.imagePath + '?t=' + new Date().getTime();
        this.cdRef.markForCheck();
      }
    });
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }

  /* Reroute to chat while sending parcel image file */
  public confirmParcel(): void {
    if (this.selectedParcelInfo) {
      this.selectedParcelInfo.isDetailedDescription = this.isDetailedDescription;
      this.selectedParcelInfo.hasBeenDescribed = false;
      this.router.navigate(['/chat']);
    }
  }
}
