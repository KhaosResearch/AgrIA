import { IEnvironment } from '../app/models/environment.model';

export const environment: IEnvironment = {
  production: true,
  isDocker: true,
  apiPort: 5000, // Standard HTTPS port for production
  apiUrl: '/api/', // Your Docker API URL
};
