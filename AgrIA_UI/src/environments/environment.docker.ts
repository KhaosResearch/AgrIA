import { IEnvironment } from "../app/models/environment.model";

export const environment: IEnvironment = {
  production: true,
  isDocker: true,
  apiPort: 5000, // Standard HTTPS port for production
  apiUrl: 'http://backend:5000', // Your Docker API URL
};