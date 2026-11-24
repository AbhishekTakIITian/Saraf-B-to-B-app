import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  message: string;
  role: 'admin' | 'user';
}

export interface NewUserRequest {
  username: string;
  password: string;
  role?: 'admin' | 'user';
}

export interface NewUserResponse {
  message: string;
  role: 'admin' | 'user';
}

export interface Client {
  id: number;
  owner_username: string;
  name: string;
  address: string | null;
  contact_number: string | null;
  created_at: string;
  last_edited_at: string;
  last_accessed_at: string | null;
}

export interface ClientStats {
  total: number;
  last_edited: Client | null;
  last_accessed: Client | null;
}

export interface ClientCreate {
  name: string;
  address?: string;
  contact_number?: string;
}

export interface ClientUpdate {
  name?: string;
  address?: string;
  contact_number?: string;
}

export interface ClientDataEntry {
  id: number;
  client_id: number;
  number: number;
  jwellery_value: number;
  description: string;
  date_created: string | null;
  date_updated: string | null;
  date_completed: string | null;
  final_value: number | null;
}

export interface ClientDataCreate {
  number: number;
  jwellery_value: number;
  description: string;
}

export interface ClientDataUpdate {
  number?: number;
  jwellery_value?: number;
  description?: string;
  final_value?: number;
}

export interface CompleteDataEntry {
  final_value: number;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  /** Base URL of the FastAPI backend — same-origin when served by backend, localhost in ng dev */
  private readonly baseUrl = this.resolveBaseUrl();

  constructor(private http: HttpClient) {}

  private resolveBaseUrl(): string {
    if (typeof window !== 'undefined' && window.location) {
      const { protocol, hostname, port } = window.location;
      if (port === '4200') {
        return 'http://localhost:8000';
      }
      if ((protocol === 'http:' || protocol === 'https:') && hostname) {
        return window.location.origin;
      }
    }
    return 'http://localhost:8000';
  }

  /**
   * POST /login
   * Sends username + password to the backend and returns the user's role.
   */
  login(credentials: LoginRequest): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.baseUrl}/login`, credentials);
  }

  /**
   * POST /users
   * Admin-only: adds a new user to the login table.
   */
  addUser(payload: NewUserRequest, requestingUser: string): Observable<NewUserResponse> {
    return this.http.post<NewUserResponse>(
      `${this.baseUrl}/users?requesting_user=${encodeURIComponent(requestingUser)}`,
      payload,
    );
  }

  /**
   * GET /clients/stats
   * Retrieves summary statistics (total, last_edited, last_accessed) for the user.
   */
  getClientStats(username: string): Observable<ClientStats> {
    return this.http.get<ClientStats>(
      `${this.baseUrl}/clients/stats?username=${encodeURIComponent(username)}`,
    );
  }

  /**
   * GET /clients
   * Lists all clients owned by the specified username.
   */
  listClients(username: string): Observable<Client[]> {
    return this.http.get<Client[]>(
      `${this.baseUrl}/clients?username=${encodeURIComponent(username)}`,
    );
  }

  /**
   * POST /clients
   * Creates a new client owned by the specified user.
   */
  createClient(payload: ClientCreate, username: string): Observable<Client> {
    return this.http.post<Client>(
      `${this.baseUrl}/clients?username=${encodeURIComponent(username)}`,
      payload,
    );
  }

  /**
   * GET /clients/{client_id}
   * Fetches a single client and updates its last_accessed_at timestamp.
   */
  getClient(clientId: number, username: string): Observable<Client> {
    return this.http.get<Client>(
      `${this.baseUrl}/clients/${clientId}?username=${encodeURIComponent(username)}`,
    );
  }

  /**
   * PUT /clients/{client_id}
   * Updates an existing client.
   */
  updateClient(clientId: number, payload: ClientUpdate, username: string): Observable<Client> {
    return this.http.put<Client>(
      `${this.baseUrl}/clients/${clientId}?username=${encodeURIComponent(username)}`,
      payload,
    );
  }

  /**
   * DELETE /clients/{client_id}
   * Deletes a client.
   */
  deleteClient(clientId: number, username: string): Observable<void> {
    return this.http.delete<void>(
      `${this.baseUrl}/clients/${clientId}?username=${encodeURIComponent(username)}`,
    );
  }

  /**
   * GET /clients/{client_id}/data
   * Fetches all data entries for a client.
   */
  getClientData(clientId: number, username: string): Observable<ClientDataEntry[]> {
    return this.http.get<ClientDataEntry[]>(
      `${this.baseUrl}/clients/${clientId}/data?username=${encodeURIComponent(username)}`,
    );
  }

  /**
   * POST /clients/{client_id}/data
   * Creates a new data entry for a client.
   */
  createClientData(clientId: number, payload: ClientDataCreate, username: string): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(
      `${this.baseUrl}/clients/${clientId}/data?username=${encodeURIComponent(username)}`,
      payload,
    );
  }

  /**
   * PUT /clients/{client_id}/data/{entry_id}
   * Updates an existing data entry for a client.
   */
  updateClientData(
    clientId: number,
    entryId: number,
    payload: ClientDataUpdate,
    username: string,
  ): Observable<{ message: string }> {
    return this.http.put<{ message: string }>(
      `${this.baseUrl}/clients/${clientId}/data/${entryId}?username=${encodeURIComponent(username)}`,
      payload,
    );
  }

  /**
   * PUT /clients/{client_id}/data/{entry_id}/complete
   * Marks a data entry as complete, setting final_value, date_completed, date_updated.
   */
  completeClientData(clientId: number, entryId: number, payload: CompleteDataEntry, username: string): Observable<{ message: string }> {
    return this.http.put<{ message: string }>(
      `${this.baseUrl}/clients/${clientId}/data/${entryId}/complete?username=${encodeURIComponent(username)}`,
      payload,
    );
  }

  /**
   * DELETE /clients/{client_id}/data/{entry_id}
   * Deletes a data entry for a client.
   */
  deleteClientData(clientId: number, entryId: number, username: string): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(
      `${this.baseUrl}/clients/${clientId}/data/${entryId}?username=${encodeURIComponent(username)}`,
    );
  }
}
