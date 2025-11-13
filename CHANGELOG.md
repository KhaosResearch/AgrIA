# 📝 Changelog – Version 1.3 (September - November 2025)

This release unifies our codebase into a single repository and introduces major enhancements to our data processing, image super-resolution capabilities, and the core Eco-scheme classification engine.

---

### 🚀 New Features & User Experience

* **Custom SIGPAC Tools (Internal Rework):** The parcel drawing tool now uses our **newly developed and updated in-house SIGPAC tools** to automatically retrieve and process parcel metadata within Spanish territory. This update replaces previous reliance on external SIGPAC API packages, improving control and reliability.
* **Precision Eco-scheme Engine:** Implemented a new **server-side algorithm** designed for **high-precision Eco-scheme classification**. This engine correctly determines not only the *assignment* of Eco-schemes but also the **rate calculation precision** based on factors like irrigation and slope coefficients (Backend).
* **Enhanced Multilingual Support:** Enhanced language consistency and fixed various UI elements (e.g., Navbar) to ensure **proper English/Spanish language switching** across the application, especially for crop classification data (Frontend/Backend).
* **Improved Image Quality (SEN2SR):** Integrated the **SEN2SR Super-Resolution pipeline** to significantly improve the resolution and clarity of Sentinel-2 satellite imagery provided for parcel analysis (Backend).
* **Improved Chat Security:** Added **security against Markdown/HTML injection** in chat replies for a safer user experience (Frontend/Backend).

---

### 🛠 Fixes & Stability Improvements

* **Parcel Drawing Updates:** Parcel geometry updates are now properly reflected across the application after changes are made in the drawer (Frontend).
* **Image Pipeline Stability:** Implemented logic for **auto-retrying data retrieval** for cloudless images and resolved various CRS (Coordinate Reference System) and color correction issues for high-quality image processing (Backend).
* **General UI Fixes:** Fixed minor issues, including proper window height for tall images and general formatting bugs (Frontend).

---

### ⚙️ Developer & Backend Enhancements

* **Monorepo Migration:** **Successfully merged the Front-end and Back-end repositories** into this single repository. This simplifies development, tooling, and contribution for all future work.
* **Advanced Super-Resolution (SR) Benchmarking:** Introduced a comprehensive **VLM (Vision-Language Model) benchmarking pipeline**, which now includes an **SR Benchmark** to test the performance of the new **SEN2SR** integration against the project's previous iteration, **SuperRes4Sentinel (SR4S)** (Backend).
* **Modular Architecture:** Refactored core LLM and image processing functions into more modular components, improving code reuse and maintainability (Backend).
* **Automated PR Workflow:** Added a GitHub Action to **automatically append a bulleted list of commits** to the end of every Pull Request description, standardizing contribution transparency (General).