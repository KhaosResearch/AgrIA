import { Component, OnInit, OnDestroy, Input, ChangeDetectionStrategy, ChangeDetectorRef, SimpleChanges } from '@angular/core';
import { interval, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-progress-bar',
  imports: [TranslateModule],
  templateUrl: './progress-bar.component.html',
  styleUrls: ['./progress-bar.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProgressBarComponent implements OnInit, OnDestroy {
  @Input() public durationInSeconds: number = 60; // Max time for the progress bar (default is 60)
  @Input() public isProcessing: boolean = false; // Controls if the progress bar is active

  public progress: number = 0; // Current progress percentage (0-100)
  public elapsedTime: number = 0; // Time passed in seconds (still tracking total seconds)
  public formattedTime: string = '00:00';

  private timerSubscription: any;
  private destroy$ = new Subject<void>();

  // New variables for smoother animation
  private intervalMs: number = 100; // Update every 100 milliseconds (10 updates per second)
  private totalMillisecondsPassed: number = 0;

  constructor(private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    if (this.isProcessing) {
      this.startProgress();
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['isProcessing']) {
      if (this.isProcessing) {
        this.startProgress();
      } else {
        this.stopProgress();
      }
    }
    if (changes['durationInSeconds'] && this.isProcessing) {
      // If duration changes while processing, restart to apply new duration
      this.stopProgress();
      this.startProgress();
    }
  }

  startProgress(): void {
    this.totalMillisecondsPassed = 0;
    this.elapsedTime = 0;
    this.progress = 0;
    this.formattedTime = this.formatTime(0);

    // Clear any existing subscription to prevent multiple timers
    this.stopProgress();
    this.destroy$ = new Subject<void>(); // Re-initialize destroy$ for new subscription

    this.timerSubscription = interval(this.intervalMs) // Update every 'intervalMs' milliseconds
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => {
        this.totalMillisecondsPassed += this.intervalMs;
        this.elapsedTime = Math.floor(this.totalMillisecondsPassed / 1000); // Only update seconds for display

        // Calculate progress based on total milliseconds
        if (this.durationInSeconds > 0) {
          const totalDurationMs = this.durationInSeconds * 1000;
          this.progress = Math.min((this.totalMillisecondsPassed / totalDurationMs) * 100, 100);
        } else {
          this.progress = 0; // Handle zero duration case
        }

        this.formattedTime = this.formatTime(this.elapsedTime);

        // Manually trigger change detection if using OnPush
        // This is crucial because the timer runs outside Angular's zones by default in some setups,
        // or just to ensure updates are reflected immediately with OnPush.
        this.cdr.detectChanges();
      });
  }

  stopProgress(): void {
    if (this.timerSubscription) {
      this.timerSubscription.unsubscribe();
      this.timerSubscription = null;
    }
    // Complete the destroy$ subject to signal all dependent observables to complete
    this.destroy$.next();
    this.destroy$.complete();
  }

  formatTime(totalSeconds: number): string {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    const pad = (num: number) => (num < 10 ? '0' : '') + num;
    return `${pad(minutes)}:${pad(seconds)}`;
  }

  ngOnDestroy(): void {
    this.stopProgress();
  }
}
