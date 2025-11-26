import { IEnvironment } from "../app/models/environment.model";

export const environment: IEnvironment = {
  production: true,
  isDocker: true,
  apiPort: 5001, // Standard HTTPS port for production
  apiUrl: `http://backend:5001`, // Your production API URL
};