import { IEnvironment } from "../app/models/environment.model";

export const environment: IEnvironment = {
  production: true,
  apiUrl: 'http://127.0.0.1:5000', // Your production API URL
  apiPort: 5000 // Standard HTTPS port for production
};