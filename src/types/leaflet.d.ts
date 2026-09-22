// Ambient declarations for Leaflet loaded dynamically via DOM
export {};

declare global {
  interface Window {
    L?: any;
  }
}
