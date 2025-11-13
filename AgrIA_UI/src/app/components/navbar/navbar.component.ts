import { Component, HostBinding, HostListener, inject } from '@angular/core';
import { RouterModule } from '@angular/router';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { DEFAULT_LANG } from '../../config/constants';


@Component({
  selector: 'app-navbar',
  imports: [
    RouterModule,
    TranslateModule
],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.css'
})
export class NavbarComponent {
  // Initialize isMenuOpen to false, meaning the menu is closed by default
  protected isMenuOpen: boolean = false;
  // Style tracking variables
  private isVisible: boolean = true;
  private lastScrollTop: number = 0;
  private isAtTop: boolean = true;
  private isHoveringTop: boolean = false;
  private maxPhoneScreenWidthPx: number = 768;
  // Translation service
  private translateService = inject(TranslateService);
  public currentLanguage: string = DEFAULT_LANG;

  constructor() {
    this.translateService.setDefaultLang(DEFAULT_LANG);
 }

  ngOnInit() {
    this.updateLanguage()
    this.updateVisibility();
  }

  @HostBinding('class.hidden') get hidden() {
    return !this.isVisible;
  }

  @HostBinding('class.visible') get visible() {
    return this.isVisible;
  }


  @HostListener('window:scroll', [])
  onWindowScroll() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    this.isAtTop = scrollTop < 80;

    if (scrollTop < this.lastScrollTop) {
      this.isVisible = true; // Scrolling up
    } else if (!this.isHoveringTop && !this.isAtTop) {
      this.isVisible = false; // Scrolling down
    }

    this.lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
  }

  @HostListener('document:mousemove', ['$event'])
  private onMouseMove(event: MouseEvent) {
    this.isHoveringTop = event.clientY < 80; // top 80px of screen

    if (this.isHoveringTop) {
      this.isVisible = true;
    } else if (!this.isAtTop && !this.isHoveringTop) {
      this.isVisible = false;
    }
  }

  @HostListener('window:resize', ['$event'])
  onResize(event: any): void {
    if (window.innerWidth > this.maxPhoneScreenWidthPx && this.isMenuOpen) {
      this.isMenuOpen = false; // Close menu if resized above breakpoint
    }
  }

  /**
   * Updates navbar visibility reactively based on scroll position and hover state.
   */
  private updateVisibility() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    this.isAtTop = scrollTop < 5;
    this.isVisible = this.isAtTop || this.isHoveringTop;
  }


  /**
   * Toggles the state of the mobile menu (open/closed).
   * This method is called when the hamburger icon is clicked.
   */
  public toggleMenu(): void {
    if (window.innerWidth < this.maxPhoneScreenWidthPx) {
      this.isMenuOpen = !this.isMenuOpen;
    }
  }

  /**
   * Closes the mobile menu.
   * This can be useful for closing the menu when a navigation link is clicked,
   * especially in a single-page application where navigating doesn't refresh the page.
   */
  public closeMenu(): void {
    this.isMenuOpen = false;
  }
  
  public switchLanguage(lang: string) {
    this.translateService.use(lang);
    this.currentLanguage = lang;
    // Cache the selected language in localStorage
    this.translateService.use(lang);
    localStorage.setItem('app_lang', lang);
  }

  /**
   * Updates current languages based on what is saved on localStorage or default.
   */
  private updateLanguage() {
    // Restore from localStorage or fallback to default
    const savedLang = localStorage.getItem('app_lang');
    this.currentLanguage = savedLang || DEFAULT_LANG;

    // Tell ngx-translate
    this.translateService.use(this.currentLanguage);
  }

}