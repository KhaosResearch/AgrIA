# 📝 Changelog – Version 1.2 (September 2025)

### 🚀 New Features
- **Enhanced Parcel Locator:** Introduced advanced search logic, including coordinate-based search and optimized parcel lookup modules.
- **Integrated Finder & Drawer:** Improved workflow for parcel discovery and custom geometry drawing, with data sharing between components.
- **UI Enhancements:** New tabbed layout for parcel tools, improved validation, and better state handling across forms.
- **Server Enrichment:** Backend now supports geometry + SIGPAC metadata parsing, with improved error handling and enriched responses.

---

### 🛠 Fixes & Improvements
- Debug outputs removed and logging cleaned up.
- Progress indicators now more accurate during parcel processing.
- Refined error messages across UI and Server.
- Additional validation and input handling improvements.

---

### 📦 Enhancements
- Auto-display of last searched parcel in chat assistant.
- Improved tile providers for better map rendering.
- Documentation updates and minor code refactors.

---

## 📁 UI-Specific Changes
- Extracted components for reusability (displayer, address search).
- Implemented polygon drawing with `leaflet-draw`.
- New form reset options and field locking logic.
- Style and folder structure refinements.

---

## 🖥️ Server-Specific Changes
- New routes for enriched parcel geometry + SIGPAC handling.
- Extended validation pipeline with more detailed error feedback.
- Integrated LLM-based description enrichment into server responses.

# 📝 Changelog – Version 1.1 (July 2025)

### 🚀 New Features
- **Parcel Drawer:** Users can now draw custom parcel geometries directly on the map. The system captures, stores, and processes this geometry.
- **Combined Parcel Finder & Drawer View:** The two tools are now integrated on the same page using tabs for seamless switching.
- **Detailed Descriptions:** Added the option to toggle between TL;DR and detailed LLM-enriched parcel descriptions.
- **SIGPAC Info Display:** New table columns for classification and crop types, with updated form to support SIGPAC data entry.
- **Multilingual Content:** Full description examples and TL;DR summaries now include both Spanish and English versions.

---

### 🛠 Fixes & Improvements
- Improved error handling across UI and backend.
- Refined notification messages (Angular Material snackbars).
- Reset buttons added for form clearing and UI control.
- Debug prints removed from backend after initial testing.
- Progress bar behavior corrected and made more informative.
- Minor fixes in UI styling, folder structure, and input validation.
- Updated documentation and README content.

---

### 📦 Enhancements
- Enriched data pipeline from UI to backend, allowing more structured and complete parcel info flow.
- New tile provider for improved map rendering.
- Auto-display of last searched parcel info in chat view.
- Backend support for enriched LLM-based content parsing and formatting.
- Support for parsing parcel geometry and SIGPAC metadata on the server side.

---

## 📁 UI-Specific Changes
- Installed `leaflet-draw` for polygon drawing.
- Cleaned up public folder structure.
- Introduced tabbed layout for Parcel Finder & Drawer.
- Implemented component-based architecture for Parcel Drawer.
- UI form includes validation and field locking based on system state.

---

## 🖥️ Server-Specific Changes
- Added routes to process and store custom geometry and metadata from the frontend.
- Integrated enriched LLM content into backend responses.
- Included logic to validate inputs, return detailed errors, and handle new SIGPAC-related payloads.
