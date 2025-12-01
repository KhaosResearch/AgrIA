export interface IEnvironment {
  production: boolean;
  isDocker: boolean;
  apiPort: number;
  apiUrl: string;
}