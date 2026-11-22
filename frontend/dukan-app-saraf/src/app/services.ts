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

@Injectable({ providedIn: 'root' })
export class ApiService {
  /** Base URL of the FastAPI backend — override via environment file for prod */
  private readonly baseUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

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
}
