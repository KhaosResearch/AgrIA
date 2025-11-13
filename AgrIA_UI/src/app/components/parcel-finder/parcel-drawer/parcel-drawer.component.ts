import * as L from 'leaflet';
import 'leaflet-draw';
import { Component, EventEmitter, inject, Input, Output, signal, WritableSignal } from '@angular/core';
import { LangChangeEvent, TranslateModule, TranslateService } from '@ngx-translate/core';
import { ParcelFinderService } from '../../../services/parcel-finder.service/parcel-finder.service';
import { FormsModule } from '@angular/forms';
import { ICropClassification, IGroupedCropClassification, IParcelDrawerGeojson, ISelectedCrop } from '../../../models/parcel-drawer.model';
import { NotificationService } from '../../../services/notification.service/notification.service';
import { IFindParcelresponse, IParcelMetadata } from '../../../models/parcel-finder.model';
import { Subscription } from 'rxjs';

// Set default icon paths
delete (L.Icon.Default.prototype as any)._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl: "public/leaflet/marker-icon-2x.png",
  iconUrl: 'public/leaflet/marker-icon.png',
  shadowUrl: 'public/leaflet/marker-shadow.png',
});

@Component({
  selector: 'app-parcel-drawer',
  imports: [
    TranslateModule,
    FormsModule,
],
  templateUrl: './parcel-drawer.component.html',
  styleUrl: './parcel-drawer.component.css'
})
export class ParcelDrawerComponent {
  // Loading process flag
  @Input() isLoading: WritableSignal<boolean> = signal(false);

  // Parcel found emmiter
  @Output() parcelFound = new EventEmitter<IFindParcelresponse>();
  // Start loading process emmiter
  @Output() loadingStarted = new EventEmitter<number>();
  // Find parcel request emmiter
  @Output() findParcelRequest = new EventEmitter<FormData>();

  // Leaflet map instance
  private map!: L.DrawMap;
  // Coordinates marker
  private activeMarker: L.Marker | null = null;
  // Map zoom level attribute
  private mapZoom: number = 5;
  // Feature group to hold drawn items
  private drawnItems = new L.FeatureGroup();
  // Flag for when a shape is being drawn
  private isDrawing: WritableSignal<boolean> = signal(false);
  // Coordinates attribute
  protected mapCenter: string = '40.400409, -3.631434';
  // Coordinates attribute
  protected coordinates: string = this.mapCenter; // TODO: REMOVE Center coordinates (40.4165, -3.70256)
  // Is coordinates in specificn zone (Spain) flag
  protected coordsInZone: WritableSignal<boolean> = signal(true);

  // Date for which the parcel image is requested
  protected selectedDate: string  = new Date().toISOString().split('T')[0];
  // Max date allowed for the date picker
  protected today: string = new Date().toISOString().split('T')[0];
  // Parcel's geometry attribute
  protected parcelGeometry: IParcelDrawerGeojson | null = null;
  // Active Tab flag
  protected activeTab: 'sigpac' | 'address' = 'sigpac';
  // List of SIGPAC's crop classifications
  protected cropClassification: ICropClassification[] = [];
  // Grouped crop classifications by type and subtype
  protected groupedCropClassification: IGroupedCropClassification = {};
  // Selected crop classifications
  protected selectedClassifications: ISelectedCrop[] = [];
  // Parcel Metadata
  private parcelMetadata: IParcelMetadata = {
    query: [],
    arboles: [],
    convergencia: {
      cat_fechaultimaconv: ''
    },
    id: [],
    isRecin: false,
    parcelaInfo: {
      agregado: 0,
      dn_surface: 0,
      municipio: '',
      parcela: 0,
      poligono: 0,
      provincia: '',
      referencia_cat: ''
    },
    usos: [],
    vigencia: '',
    vuelo: {
      fecha_vuelo: 0
    }
  };
  // Selected parcel response information
  protected selectedParcelInfo: IFindParcelresponse | null = null;
  // Detailed description flag
  protected isDetailedDescription: boolean = false;
  // Valid input flag
  protected isValidInput: WritableSignal<boolean> = signal(true);
  // Max Loading Time
  private maxLoadingDuration: number = 60;

  // Service to handle parcel finding operations
  private parcelFinderService: ParcelFinderService = inject(ParcelFinderService);
  // Service for notifications
  private notificationService: NotificationService = inject(NotificationService);
  // Translation service
  private translateService = inject(TranslateService);
  // Utility to get object keys
  protected objectKeys = Object.keys;
  // Subscription handler
  private subscription = new Subscription();

  constructor() { }
  
  ngOnInit() {
    // Initial load
    this.loadCropClassifications();

    // Subscribe to language changes
    this.subscription.add(
      this.translateService.onLangChange.subscribe((event: LangChangeEvent) => {
        console.log('Language changed to:', event.lang);
        this.resetForm()
        this.loadCropClassifications();
      })
    );
  }
  /**
   * Initializes the map and loads the provider layer.
   */
  ngAfterViewInit(): void {
    this.initMap();
  }

  ngOnDestroy() {
    this.subscription.unsubscribe();
  }
  
  /**
   * Initializes the map with a default center and zoom level, sets up the tile layer, and adds drawing controls.
   */
  private initMap(): void {
    // Initialize the map with a default center and zoom level
    this.map = L.map('map', {
      center: [Number(this.mapCenter.split(',')[0].trim()), Number(this.mapCenter.split(',')[1].trim())],
      zoom: this.mapZoom,
    });
    // Set the map view to the default coordinates
    const tiles = L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      {
        maxZoom: 20,
        minZoom: 3,
        attribution:
          'Tiles &copy; Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community',
      }
    );
    tiles.addTo(this.map);

    // Use persistent FeatureGroup to hold drawn items
    this.map.addLayer(this.drawnItems);

    // Initialize the draw control and pass it the FeatureGroup of editable layers
    const drawControl = new L.Control.Draw({
      edit: {
        featureGroup: this.drawnItems,
      },
      draw: {
        polygon: {},
        polyline: false,
        rectangle: false,
        circle: false,
        marker: false,
        circlemarker: false,
      },
    });

    this.map.addControl(drawControl);
    
    this.mapEventHandling();
  }

  /**
   * Handler for relevant map events.
   * 
   */
  private mapEventHandling() {
    this.setupDrawEvents();
    this.setupClickHandler();
  }

  /**
   * Drawing, editing and deleting layers' event handlers.
   * 
   */
  private setupDrawEvents() {
    // Start of drawing/editing/deleting → enable drawing state
    this.map.on(L.Draw.Event.DRAWSTART, () => this.isDrawing.set(true));
    this.map.on(L.Draw.Event.EDITSTART, () => this.isDrawing.set(true));
    this.map.on(L.Draw.Event.DELETESTART, () => this.isDrawing.set(true));

    // End of drawing/editing/deleting → disable drawing state
    this.map.on(L.Draw.Event.DRAWSTOP, () => this.isDrawing.set(false));
    this.map.on(L.Draw.Event.EDITSTOP, () => this.isDrawing.set(false));
    this.map.on(L.Draw.Event.DELETESTOP, () => this.isDrawing.set(false));

    // When a new shape is created
    this.map.on(L.Draw.Event.CREATED, (event: any) => {
      this.drawnItems.clearLayers();
      const layer = event.layer;
      this.drawnItems.addLayer(layer);

      // Convert  to GeoJSON and store it in parcelGeometry
      this.parcelGeometry = layer.toGeoJSON().geometry as IParcelDrawerGeojson;
      this.parcelGeometry.CRS = 'epsg:4326';
    });

    // When existing shapes are modified
    this.map.on(L.Draw.Event.EDITED, (event: any) => {
      event.layers.eachLayer((layer: any) => {
        // Convert updated geometry to GeoJSON and save it
        this.parcelGeometry = layer.toGeoJSON().geometry as IParcelDrawerGeojson;
        this.parcelGeometry.CRS = 'epsg:4326';
      });
    });

    // When features are deleted
    this.map.on(L.Draw.Event.DELETED, () => {
      this.parcelGeometry = null;
    });
  }

  /**
   * Coordinates markers' related click event handler.
   */
  private setupClickHandler() {
    this.map.on('click', (e: L.LeafletMouseEvent) => {
      if (this.isDrawing()) {
        return;
      }

      const lat = e.latlng.lat.toFixed(6);
      const lng = e.latlng.lng.toFixed(6);
      const coords = `${lat}, ${lng}`;
      console.log('Clicked coordinates:', coords);
      
      const formData = new FormData();
      formData.append('lat', lat ? lat : 'None');
      formData.append('lng', lng ? lng : 'None');
      this.parcelFinderService.isCoordInZone(formData).subscribe({
        next: (inZone: boolean) => {
          this.coordsInZone.set(inZone);
          console.log("Zone check result:", inZone);
          if (inZone) {
            console.log("✅ The coordinates are within a Spanish zone!");
          } else {
            console.log("❌ The coordinates are outside all Spanish zones.");

          }
        },
        error: err =>{
          console.error("Error checking coordinates:", err)
          this.coordsInZone.set(false);
        }
      });


        // Copy coordinates to clipboard
        navigator.clipboard.writeText(coords)
        .then(() => {
          if (this.map) {
            this.resetCoordinatesMarker(parseFloat(lat), parseFloat(lng));
            this.coordinates = coords;
            this.notificationService.showNotification(
              'parcel-drawer.coordinates.new-coordinates',
              coords,
              'info'
            );
          }
        })
        .catch(err => {
          console.error('Failed to copy coordinates:', err);
          this.notificationService.showNotification(
            'parcel-drawer.coordinates.new-coordinates',
            err,
            'error'
          );
        });
    });
  }

  /**
   * Reset coordinate marker placing and info.
   * 
   * @param lat - latitude component.
   * @param lng - Longitude component.
   */
  private resetCoordinatesMarker(lat: number, lng: number) {
    if (this.activeMarker) {
      this.map.removeLayer(this.activeMarker);
    }
    const coords = `${lat}, ${lng}`;

    // Create new marker
    this.activeMarker = L.marker([lat, lng])
      .addTo(this.map)
      .bindPopup(`Coord: ${coords}`)
      .openPopup();
  }

  /**
   * Centers the map on the provided coordinates and sets a closer zoom level.
   * 
   * @returns The current map instance.
   */
  protected centerMapOnCoordinates(): void {
    this.mapZoom = this.mapZoom < 17? 17 : this.mapZoom; // Limit zoom level to a maximum of 16
    if (!this.map || !this.coordinates) return;

    const coords = this.coordinates
      .split(',')
      .map(coord => parseFloat(coord.trim()));

    if (coords.length === 2 && !coords.some(isNaN)) {
      const latlng = L.latLng(coords[0], coords[1]);
      this.map.setView(latlng, this.mapZoom);
    } else {
      this.notificationService.showNotification("parcel-drawer.coordinates.invalid", this.coordinates, "error", 10000);
      console.warn('Invalid coordinates format:', this.coordinates);
    }

    this.resetCoordinatesMarker(coords[0], coords[1])
    this.scrollToMap();
  }

  /**
   * Scrolls view to map element.
   */
  private scrollToMap(): void {
    const mapElement = document.getElementById('map');
    if (mapElement) {
      mapElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }


  /**
   * Resets the map view to the default coordinates and zoom level, clearing any drawn shapes.
   */
  protected resetMapAndCoordinates(): void {
    this.parcelGeometry = null;
    this.drawnItems.clearLayers();
    this.mapZoom = 5;
    if (this.activeMarker) {
      this.map.removeLayer(this.activeMarker);
    }

    this.coordinates = this.mapCenter;
    const coords = this.coordinates.split(',').map(coord => parseFloat(coord.trim()));

    const latlng = L.latLng(coords[0], coords[1]);
    this.map?.setView(latlng, this.mapZoom);
   this.coordinates = '';
   this.resetForm()
  }

  /**
   * Loads crop classifications from the service and groups them by type and subtype.
   */
  private loadCropClassifications() {
    this.parcelFinderService.loadCropClassifications(this.translateService.currentLang).subscribe(
      (cropClassification: ICropClassification[]) => {
        this.cropClassification = cropClassification;
        this.groupedCropClassification = this.groupByTypeAndSubtype(cropClassification);

      },
      (error) => {
        this.notificationService.showNotification("parcel-finder.sigpac-table.error", `\n${error.error.error}`, "error", 10000);
        console.error('Error loading crop classifications:', error);
      }
    );
  }

  /**
   * Groups crop classifications by type and subtype.
   * 
   * @param data - Array of crop classifications to be grouped.
   * @returns An object where keys are types and values are objects with subtypes as keys.
   */
  private groupByTypeAndSubtype(data: ICropClassification[]) {
    const grouped: any = {};
      for (const item of data) {
        const type = item.type || 'Unknown';
        const subtype = item.subtype1 || item.subtype2 || '\u2610';
        if (!grouped[type]) grouped[type] = {};
        if (!grouped[type][subtype]) grouped[type][subtype] = [];
        grouped[type][subtype].push(item);
      }
      return grouped;
  }

  /**
   * Toggles the selection state of a crop classification item and adds/removes it to/from selection.
   * 
   * @param clickedItem - The crop classification item to toggle.
   */
  protected toggleSelectedClassification(clickedItem: ICropClassification): void {
    const index = this.selectedClassifications.findIndex(
      (entry) => entry.classification === clickedItem
    );

    if (index === -1) {
      this.selectedClassifications.push({
        classification: clickedItem,
        surface: null,
        irrigation: null
      });
    } else {
      this.selectedClassifications.splice(index, 1);
    }
  }

  /**
   * Checks if a crop classification item is selected.∫
   * 
   * @param item - The crop classification item to check.
   * @returns 
   */
  protected isSelected(item: ICropClassification): boolean {
  return this.selectedClassifications.some(
    (entry) => entry.classification === item
  );
}

  /**
   * Checks if a crop classification item is selected.
   * 
   * @param item - The selected crop classification item.
   * @returns The class (title) of the item if it is selected, otherwise an empty string.
   */
  protected trackClassification(item: ISelectedCrop): string {
    return item.classification.class;
  }

  /**
   * Sends the parcel geometry and metadata to the backend for processing.
   *  
   */
  protected sendParcelDrawerInfo(): void {
    try {
      // Validate all input before sending
      this.validateInput();

      // Init loading notifications
      this.notificationService.showNotification("parcel-finder.searching", "", "info")
      this.isLoading.set(true);
      this.loadingStarted.emit(this.maxLoadingDuration);
      document.body.style.cursor = 'progress';

      // Add essential metadata from crop classification to request
      if(this.selectedClassifications.length > 0){
        this.parcelMetadata.usos = [];  // Reset metadata info
        for (const classification of this.selectedClassifications) {
          const item = classification.classification
            this.parcelMetadata.usos.push({
              dn_superficie: Number(String(classification.surface).replace(",", ".")) * 10000,
              uso_sigpac: `${item.class}-${item.name}`,
              superficie_admisible: Number(String(classification.surface).replace(",", ".")) * 10000,
            });
        };
      }
      // Build and send request form
      const formData = new FormData();
      formData.append('parcelGeometry', this.parcelGeometry ? JSON.stringify(this.parcelGeometry) : 'None');
      formData.append('parcelMetadata', this.parcelMetadata ? JSON.stringify(this.parcelMetadata) : 'None');
      formData.append('coordinates', this.coordinates ? this.coordinates : 'None');
      formData.append('selectedDate', this.selectedDate);
      formData.append('isFromCadastralReference', "False");

      console.log("this.parcelMetadata", this.parcelMetadata)

      // Output request to parcel finder component
      this.findParcelRequest.emit(formData)
    } catch (err) {
      if(this.isValidInput()) {
        this.notificationService.showNotification("parcel-finder.error",`\n${err}`,"error", 10000)
      }
      console.error("Request error:", err);
    }
  }

  /**
   * Validate the parcel geometry and selected classifications
   */
  private validateInput() {
    this.isValidInput.set(false);

    if (!this.parcelGeometry && (!this.activeMarker || this.coordinates == '')) { // TODO: REMOVE WHEN IMPLEMENTED
      const message = "No coordinate marker found. Place one in your Spanish parcel or draw your parcel if out of Spain";
      this.notificationService.showNotification(
        "parcel-drawer.missing.parcel-drawing", "", "error", 10000
      );
      throw new Error(message);
    }
    else if(!this.coordsInZone())
    {
      if (!this.parcelGeometry) {
        const message = "No parcel drawing found. You need to draw the parcel limits when outside of Spain";
        this.notificationService.showNotification(
          "parcel-drawer.missing.parcel-out", "", "error", 10000
        );
        throw new Error(message);
      }
      else if (!this.selectedClassifications || this.selectedClassifications.length === 0) {
        const message = "No crop classification selected for parcel geometry.";
        this.notificationService.showNotification(
          "parcel-drawer.missing.crop-classification", "", "error", 10000
        );
        throw new Error(message);
      }
      else if (this.selectedClassifications.some(item => item.surface === null)) {
        const message = "Some selected crop classifications have missing surface values.";
        this.notificationService.showNotification(
          "parcel-drawer.missing.surface", "", "error", 10000
        );
        throw new Error(message);
      }
    }
    this.isValidInput.set(true);
  }

  protected resetForm(): void {
    console.log("cropClassification", this.cropClassification)
    console.log("groupedCropClassification", this.groupedCropClassification)
    console.log("selectedClassifications", this.selectedClassifications)
    this.selectedClassifications = [];
  }
  
}
