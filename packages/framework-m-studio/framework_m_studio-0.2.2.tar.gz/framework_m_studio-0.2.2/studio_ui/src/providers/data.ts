/**
 * Framework M Studio Data Provider
 * 
 * Maps Refine's DataProvider interface to Framework M's REST API.
 * 
 * API Endpoints:
 * - GET /studio/api/doctypes -> List all DocTypes
 * - GET /studio/api/doctype/{name} -> Get single DocType
 * - POST /studio/api/doctype/{name} -> Create/Update DocType
 * - DELETE /studio/api/doctype/{name} -> Delete DocType
 */

import type { DataProvider } from "@refinedev/core";
import { API_URL } from "./constants";

/**
 * Custom data provider for Framework M Studio API
 */
export const dataProvider: DataProvider = {
  getApiUrl: () => API_URL,

  getList: async ({ resource }) => {
    const url = `${API_URL}/${resource}`;
    
    const response = await fetch(url);
    const data = await response.json();
    
    // Framework M returns { doctypes: [...], count: N }
    return {
      data: data.doctypes || data.data || data,
      total: data.count || data.total || (data.doctypes?.length ?? 0),
    };
  },

  getOne: async ({ resource, id }) => {
    // For doctypes, use /doctype/{name} endpoint
    const endpoint = resource === "doctypes" ? "doctype" : resource;
    const url = `${API_URL}/${endpoint}/${id}`;
    
    const response = await fetch(url);
    const data = await response.json();
    
    return { data };
  },

  create: async ({ resource, variables }) => {
    const endpoint = resource === "doctypes" ? "doctype" : resource;
    const name = (variables as { name: string }).name;
    const url = `${API_URL}/${endpoint}/${name}`;
    
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(variables),
    });
    const data = await response.json();
    
    return { data };
  },

  update: async ({ resource, id, variables }) => {
    const endpoint = resource === "doctypes" ? "doctype" : resource;
    const url = `${API_URL}/${endpoint}/${id}`;
    
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(variables),
    });
    const data = await response.json();
    
    return { data };
  },

  deleteOne: async ({ resource, id }) => {
    const endpoint = resource === "doctypes" ? "doctype" : resource;
    const url = `${API_URL}/${endpoint}/${id}`;
    
    const response = await fetch(url, { method: "DELETE" });
    const data = await response.json();
    
    return { data };
  },

  getMany: async ({ resource, ids }) => {
    const promises = ids.map(id => 
      dataProvider.getOne!({ resource, id, meta: {} })
    );
    const results = await Promise.all(promises);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return { data: results.map(r => r.data) as any };
  },

  custom: async ({ url, method, payload, headers }) => {
    const response = await fetch(url, {
      method: method || "GET",
      headers: { "Content-Type": "application/json", ...headers },
      body: payload ? JSON.stringify(payload) : undefined,
    });
    const data = await response.json();
    return { data };
  },
};
