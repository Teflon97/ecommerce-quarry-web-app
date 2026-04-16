import React, { useState, useRef, useEffect, useCallback } from 'react';
import type { DeliveryLocation } from '../types';
import { MMAMASHIA_COORDS } from '../constants';

// Declare the 'L' global variable provided by the Leaflet.js script
declare var L: any;

interface MapModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLocationSelect: (location: DeliveryLocation) => void;
}

// Gaborone: -24.6581, 25.9087
// Mochudi: -24.4167, 26.1500
const GABORONE_COORDS = { lat: -24.6581, lng: 25.9087 };
const MOCHUDI_COORDS = { lat: -24.4167, lng: 26.1500 };

const latDiff = MOCHUDI_COORDS.lat - GABORONE_COORDS.lat;
const lngDiff = MOCHUDI_COORDS.lng - GABORONE_COORDS.lng;
const INITIAL_CENTER = {
  lat: GABORONE_COORDS.lat + latDiff * 0.5,
  lng: GABORONE_COORDS.lng + lngDiff * 0.5,
};
const INITIAL_ZOOM = 11;
const INITIAL_PIN_POSITION = MMAMASHIA_COORDS;

const MapModal: React.FC<MapModalProps> = ({ isOpen, onClose, onLocationSelect }) => {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markerRef = useRef<any>(null);

  const [markerPosition, setMarkerPosition] = useState<{ lat: number; lng: number }>(INITIAL_PIN_POSITION);
  const [currentAddress, setCurrentAddress] = useState<string>('Fetching address...');
  const [isConfirming, setIsConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateAddress = useCallback(async (lat: number, lng: number) => {
    setCurrentAddress('Fetching address...');
    try {
      const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}`);
      if (!response.ok) {
        throw new Error('Failed to fetch address');
      }
      const data = await response.json();
      const address = data.display_name || `Pinned Location: ${lat.toFixed(5)}, ${lng.toFixed(5)}`;
      setCurrentAddress(address);
    } catch (e) {
      console.error("Reverse geocoding failed:", e);
      setCurrentAddress(`Address lookup failed. Coordinates: ${lat.toFixed(5)}, ${lng.toFixed(5)}`);
    }
  }, []);
  
  const initMap = useCallback(() => {
    if (!mapRef.current || mapInstanceRef.current) return;
    
    try {
      const map = L.map(mapRef.current).setView([INITIAL_CENTER.lat, INITIAL_CENTER.lng], INITIAL_ZOOM);
      mapInstanceRef.current = map;

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      }).addTo(map);

      L.circle([MMAMASHIA_COORDS.lat, MMAMASHIA_COORDS.lng], {
          radius: 15000, // 15km in meters
          color: '#10b981',
          fillColor: '#10b981',
          fillOpacity: 0.15
      }).addTo(map).bindPopup("15km Free Delivery Radius");

      const marker = L.marker([INITIAL_PIN_POSITION.lat, INITIAL_PIN_POSITION.lng], {
        draggable: true,
        title: "Drag me to your delivery location"
      }).addTo(map);

      markerRef.current = marker;

      marker.on('dragend', (event: any) => {
        const newPos = event.target.getLatLng();
        setMarkerPosition({ lat: newPos.lat, lng: newPos.lng });
      });
      
      // Crucial for responsive resizing
      setTimeout(() => map.invalidateSize(), 100);

    } catch (e) {
      console.error("Leaflet map initialization failed:", e);
      setError("Could not load the map. Please try again.");
    }
  }, []);
  
  useEffect(() => {
    if (isOpen) {
      setError(null);
      if (typeof L !== 'undefined') {
        // Delay init to allow modal transition to finish
        const timer = setTimeout(() => {
          initMap();
          setMarkerPosition(INITIAL_PIN_POSITION);
          updateAddress(INITIAL_PIN_POSITION.lat, INITIAL_PIN_POSITION.lng);
        }, 10);
        return () => clearTimeout(timer);
      } else {
        setError("Map library could not be loaded. Please check your internet connection.");
      }
    } else {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
        markerRef.current = null;
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);
  
  useEffect(() => {
      if (isOpen && markerPosition) {
          updateAddress(markerPosition.lat, markerPosition.lng);
      }
  }, [markerPosition, isOpen, updateAddress]);

  const handleConfirmLocation = async () => {
      setIsConfirming(true);
      setError(null);

      if (!markerPosition) {
          setError("No location selected.");
          setIsConfirming(false);
          return;
      }
      
      const finalAddress = currentAddress.startsWith('Fetching') || currentAddress.startsWith('Address lookup failed') 
        ? `Pinned Location: ${markerPosition.lat.toFixed(5)}, ${markerPosition.lng.toFixed(5)}`
        : currentAddress;

      const newLocation: DeliveryLocation = {
          type: 'manual',
          address: finalAddress,
          lat: markerPosition.lat,
          lng: markerPosition.lng,
      };
      onLocationSelect(newLocation);
      setIsConfirming(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-surface rounded-lg shadow-2xl p-6 w-full max-w-4xl max-h-[90vh] flex flex-col">
        {/* Non-scrolling Header */}
        <div className="flex-shrink-0">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold">Pin Your Delivery Location</h2>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-800 text-3xl leading-none">&times;</button>
          </div>
          <p className="text-gray-600 mb-4">Drag the pin to your precise delivery address. The green circle shows the 15km free delivery zone.</p>
        </div>
        
        {/* Scrollable Content Area */}
        <div className="flex-grow overflow-y-auto min-h-0">
          <div
            ref={mapRef}
            className="relative w-full bg-gray-200 rounded-lg overflow-hidden"
            style={{ height: '40vh', minHeight: '300px' }}
          >
            {error && <div className="w-full h-full flex items-center justify-center text-red-500 p-4 text-center">{error}</div>}
          </div>
          
          <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <h3 className="font-bold text-gray-800 mb-2">Selected Location:</h3>
              <div className="space-y-1">
                  <p className="text-sm text-gray-700">
                      <span className="font-semibold w-24 inline-block">Coordinates:</span> 
                      {markerPosition ? `${markerPosition.lat.toFixed(5)}, ${markerPosition.lng.toFixed(5)}` : 'N/A'}
                  </p>
                  <p className="text-sm text-gray-700">
                      <span className="font-semibold w-24 inline-block">Address:</span> 
                      {currentAddress}
                  </p>
              </div>
          </div>
        </div>
        
        {/* Non-scrolling Footer */}
        <div className="mt-6 flex-shrink-0 flex flex-col sm:flex-row justify-end gap-4">
            <button onClick={onClose} className="bg-gray-200 text-secondary font-bold py-2 px-6 rounded-lg hover:bg-gray-300">
                Cancel
            </button>
            <button
                onClick={handleConfirmLocation}
                disabled={isConfirming || !markerPosition}
                className="bg-primary text-white font-bold py-2 px-6 rounded-lg hover:bg-orange-600 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
                {isConfirming ? 'Confirming...' : 'Confirm Location'}
            </button>
        </div>
      </div>
    </div>
  );
};

export default MapModal;
