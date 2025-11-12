# 📝 Changelog – Version 1.2 (September 2025)

### 🚀 New Features
- **Parcel Locator Enhancements:**
  - Added ability to find parcels by address and cadastral reference.
  - Implemented coordinates-based parcel search with marker placement on the map.
- **UI Component Refactor:**
  - Extracted parcel displayer and locator logic into separate reusable components.
  - Enabled data sharing between child components (cadastral, drawer, displayer).
- **Map Improvements:**
  - Added support for multiple marker options when searching by coordinates.
  - Updated Leaflet integration with new drawing and display features.

---

### 🛠 Fixes & Improvements
- Fixed parcel info caching issues and minor typos in UI.
- Refined input validation and improved error handling in search workflows.
- Added JSDoc documentation for components and services.
- Updated Angular dependencies and adjusted build configuration.
- Minor style fixes and UI consistency updates (logos, folder organization).

---

## 📁 UI-Specific Changes
- Completed implementation of parcel-locator interface with parent/child logic separation.
- Optimized search logic by extracting it into independent modules.
- Introduced address-based search flow integrated with parcel finder.
- Restructured public folder and grouped related UI components together.
- Improved translation files and updated multilingual support.

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
- Minor fixes in UI styling, folder structure, and input validation.

---

## 📁 UI-Specific Changes
- Installed `leaflet-draw` for polygon drawing.
- Cleaned up public folder structure.
- Introduced tabbed layout for Parcel Finder & Drawer.
- Implemented component-based architecture for Parcel Drawer.
- UI form includes validation and field locking based on system state.