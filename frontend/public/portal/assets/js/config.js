// API Configuration - automatically uses correct URL based on environment
const getApiBase = () => {
  // Check if we're on localhost
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://localhost:5000/api';
  }
  
  // Production: Use deployed Railway backend URL
  return 'https://hack-vento-2k26-production.up.railway.app/api';
};

const API_BASE = getApiBase();

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
  module.exports = API_BASE;
}
