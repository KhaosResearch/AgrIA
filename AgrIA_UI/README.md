# AgrIA_UI

![Angular](https://img.shields.io/badge/Angular-v20.1.4-DD0031?logo=angular&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-~5.8.3-3178C6?logo=typescript&logoColor=white)
![Leaflet](https://img.shields.io/badge/Leaflet-1.9.4-199900?logo=leaflet&logoColor=white)
![Angular Material](https://img.shields.io/badge/Material-20.1.4-3f51b5?logo=angular&logoColor=white)
![RxJS](https://img.shields.io/badge/RxJS-~7.8.0-B7178C?logo=reactivex&logoColor=white)
![Prettier](https://img.shields.io/badge/code_style-prettier-ff69b4?logo=prettier&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-Proxy-009639?logo=nginx&logoColor=white)

This project was generated using [Angular CLI](https://github.com/angular/angular-cli) version 19.2.8.

## Installation:
This is a guide to install all necessary components to run the frontend interface.

### Requirements:
- NodeJs Node Package Manager (`npm`) ( [npmjs.com](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)).
- Angular CLI (easy to get if you have `npm` by just using `npm install -g @angular/cli`).

### Setup
After getting `npm` and all requirements, install al dependencies with:
```bash
npm install
```
Follow the instructions if prompted for anything and done!

## Development server

To start a local development server, run:

```bash
ng serve
```

Once the server is running, open your browser and navigate to `http://localhost:4200/`. The application will automatically reload whenever you modify any of the source files.

## Project dirextory structure:
```bash
Agria_UI
│
├── angular.json                          # Angular workspace configuration (build, serve, test targets).
├── Dockerfile                            # Docker instructions to build the UI image (Angular + Nginx).
├── nginx.conf                            # Nginx configuration for serving the compiled Angular app.
├── karma.conf.js                         # Karma configuration for unit testing.
├── package.json                          # Project dependencies, scripts, and Angular tooling versions.
├── package-lock.json                     # Locked dependency tree for reproducible installs.
├── README.md                             # UI project documentation and setup instructions.
│
├── public                                # Static assets served as-is (not bundled by Angular).
│   ├── data                              # Static domain data used by the UI (CSV/JSON lookups).
│   │   ├── crop_classification.csv       # Crop classification reference data.
│   │   ├── crop_classification_en.json   # Localized crop classification (EN).
│   │   ├── crop_classification_es.json   # Localized crop classification (ES).
│   │   └── sigpac_location_data.json     # SIGPAC-related geographic/location metadata.
│   │
│   ├── i18n                              # Internationalization files loaded at runtime.
│   │   ├── en.json
│   │   └── es.json
│   │
│   ├── img                               # Static UI images and icons.
│   │   └── *.jpg / *.png
│   │
│   └── favicon.ico                       # Application favicon.
│
├── src                                   # Angular application source code.
│   ├── index.html                        # Main HTML entrypoint for the Angular app.
│   ├── main.ts                           # Application bootstrap (Angular 20 standalone setup).
│   ├── styles.css                        # Global application styles.
│   │
│   ├── environments                     # Environment-specific runtime configuration.
│   │   ├── environment.ts               # Default / production environment configuration.
│   │   ├── environment.development.ts   # Local development environment variables.
│   │   └── environment.docker.ts        # Docker-based deployment configuration.
│   │
│   └── app                               # Core application logic and UI architecture.
│       ├── *.css / *.html / *.ts / *spec.ts
│       │
│       ├── app.config.ts                 # Global application providers (standalone Angular config).
│       ├── app.routes.ts                 # Application route definitions.
│       │
│       ├── config                        # UI-level configuration and constants.
│       │   └── constants.ts              # Shared UI constants (filepaths).
│       │
│       ├── models                        # TypeScript domain models and interfaces for each component.
│       │   └── *.ts
│       │
│       ├── services                      # Application services (API calls, shared state, utilities).
│       │   ├── chat.service
│       │   │   └── *.ts / *.spec.ts
│       │   │
│       │   ├── chat-assistant.service
│       │   │   └── *.ts / *.spec.ts
│       │   │
│       │   ├── parcel-finder.service
│       │   │   └── *.ts / *.spec.ts
│       │   │
│       │   └── notification.service
│       │       └── *.ts / *.spec.ts
│       │
│       └── components                    # Feature-based UI components (intentional grouping).
│           ├── home-page                 # Landing / home page components.
│           │   └── *.css / *.html / *.ts / *spec.ts
│           │
│           ├── navbar                    # Application navigation bar.
│           │   └── *.css / *.html / *.ts / *spec.ts
│           │
│           ├── chat                      # Chat feature UI components.
│           │   ├── *.css / *.html / *.ts / *spec.ts
│           │   │
│           │   └── chat-assistant        # Embedded chat assistant UI.
│           │       └── *.css / *.html / *.ts / *spec.ts
│           │
│           ├── parcel-finder             # Parcel finder feature components.
│           │   ├── *.css / *.html / *.ts / *spec.ts
│           │   │
│           │   ├── parcel-cadastral      # Cadastral parcel finder view.
│           │   │   └── *.css / *.html / *.ts / *spec.ts
│           │   │
│           │   ├── parcel-locator        # Address and location-based parcel finder view.
│           │   │   └── *.css / *.html / *.ts / *spec.ts
│           │   │
│           │   ├── parcel-display        # Parcel imagery display.
│           │   │   └── *.css / *.html / *.ts / *spec.ts
│           │   │
│           │   └── parcel-drawer         # Map-based parcel finder view.
│           │       └── *.css / *.html / *.ts / *spec.ts
│           │
│           └── progress-bar              # Reusable progress/loading indicator component.
│               └── *.css / *.html / *.ts / *spec.ts
│
├── tsconfig.json                         # Base TypeScript configuration.
├── tsconfig.app.json                     # TypeScript config for the Angular application.
└── tsconfig.spec.json                    # TypeScript config for unit tests.
```

<details>
    <summary style="font-size: larger; font-weight: bold;">Expand for more useful Angular commands for developers.</summary>

## Code scaffolding

Angular CLI includes powerful code scaffolding tools. To generate a new component, run:

```bash
ng generate component component-name
```

For a complete list of available schematics (such as `components`, `directives`, or `pipes`), run:

```bash
ng generate --help
```

## Building

To build the project run:

```bash
ng build
```

This will compile your project and store the build artifacts in the `dist/` directory. By default, the production build optimizes your application for performance and speed.

## Running unit tests

To execute unit tests with the [Karma](https://karma-runner.github.io) test runner, use the following command:

```bash
ng test
```

## Running end-to-end tests

For end-to-end (e2e) testing, run:

```bash
ng e2e
```

Angular CLI does not come with an end-to-end testing framework by default. You can choose one that suits your needs.
</details>

## Additional Resources

For more information on using the Angular CLI, including detailed command references, visit the [Angular CLI Overview and Command Reference](https://angular.dev/tools/cli) page.
