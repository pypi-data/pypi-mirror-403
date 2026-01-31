import { k as axios } from "./index-bcuE0Z0p.js";
const API_BASE_URL = "/secrets/secrets";
class SecretsApi {
  /**
   * Fetches the list of secrets from the API
   */
  static async getAll() {
    try {
      const response = await axios.get(API_BASE_URL);
      return response.data;
    } catch (error) {
      console.error("API Error: Failed to load secrets:", error);
      throw error;
    }
  }
  /**
   * Adds a new secret via the API
   */
  static async create(secretData) {
    var _a, _b;
    try {
      await axios.post(API_BASE_URL, secretData);
    } catch (error) {
      console.error("API Error: Failed to add secret:", error);
      const errorMsg = ((_b = (_a = error.response) == null ? void 0 : _a.data) == null ? void 0 : _b.detail) || "Failed to add secret";
      throw new Error(errorMsg);
    }
  }
  /**
   * Fetches the actual value of a specific secret for copying
   */
  static async getValue(secretName) {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/${encodeURIComponent(secretName)}`
      );
      return response.data.value;
    } catch (error) {
      console.error("API Error: Failed to get secret value:", error);
      throw error;
    }
  }
  /**
   * Deletes a secret via the API
   */
  static async delete(secretName) {
    try {
      await axios.delete(`${API_BASE_URL}/${encodeURIComponent(secretName)}`);
    } catch (error) {
      console.error("API Error: Failed to delete secret:", error);
      throw error;
    }
  }
}
const fetchSecretsApi = SecretsApi.getAll;
const addSecretApi = SecretsApi.create;
const getSecretValueApi = SecretsApi.getValue;
const deleteSecretApi = SecretsApi.delete;
export {
  SecretsApi as S,
  addSecretApi as a,
  deleteSecretApi as d,
  fetchSecretsApi as f,
  getSecretValueApi as g
};
