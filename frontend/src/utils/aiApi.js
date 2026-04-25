import axios from 'axios';

const aiApi = axios.create({
  baseURL: 'http://localhost:8002/api/v1',
});

export default aiApi;
