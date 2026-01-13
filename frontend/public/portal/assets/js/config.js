// API Configuration - automatically uses correct URL based on environment
const getApiBase = () => {
  // Check if we're on localhost
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://localhost:5000/api';
  }
  
  // Production: Use environment variable or deployed backend URL
  // REPLACE THIS URL after deploying backend to Railway
  return 'https://your-backend-url.up.railway.app/api';
};

const API_BASE = getApiBase();

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
  module.exports = API_BASE;
}
