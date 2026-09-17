import { Injectable, PLATFORM_ID, inject } from '@angular/core';
import { HttpClient, HttpHeaders }          from '@angular/common/http';
import { Observable }                       from 'rxjs';
import { isPlatformBrowser }               from '@angular/common';

@Injectable({ providedIn: 'root' })
export class AuthService {

  private apiUrl    = 'http://localhost:5000/api';
  /** Backend origin (no /api suffix) — use to build absolute URLs for server-served files like /uploads/... */
  readonly apiOrigin = 'http://localhost:5000';
  private platformId = inject(PLATFORM_ID);

  constructor(private http: HttpClient) {}

  // ── Helper for authenticated requests ─────
  private authHeaders(): HttpHeaders {
    const token = this.getToken();
    return new HttpHeaders({
      Authorization: `Bearer ${token ?? ''}`
    });
  }

  // ── Auth ───────────────────────────────────
  signin(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/signin`, data);
  }

  signup(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/signup`, data);
  }

  // ── Profile ────────────────────────────────
  getProfile(): Observable<any> {
    return this.http.get(`${this.apiUrl}/profile`, { headers: this.authHeaders() });
  }

  /** Update name, phone, dob on the server */
  updateProfile(data: { name?: string; phone?: string; dob?: string }): Observable<any> {
    return this.http.put(`${this.apiUrl}/profile`, data, { headers: this.authHeaders() });
  }

  /**
   * Upload profile photo as a File object (multipart form).
   * The backend saves it to /uploads/profiles/.
   */
  uploadPhoto(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('photo', file);
    // IMPORTANT: do NOT set Content-Type manually – the browser will add the boundary
    return this.http.post(`${this.apiUrl}/profile/photo`, formData, {
      headers: new HttpHeaders({ Authorization: `Bearer ${this.getToken() ?? ''}` })
    });
  }

  /**
   * Upload profile photo as a base64 data URL string.
   * The backend will store the base64 directly in the database.
   */
  uploadPhotoBase64(base64: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/profile/photo`, { photoBase64: base64 }, { headers: this.authHeaders() });
  }

  // ── Settings ───────────────────────────────
  getSettings(): Observable<any> {
    return this.http.get(`${this.apiUrl}/settings`, { headers: this.authHeaders() });
  }

  updateSettings(settings: {
    emailNotifications?: boolean;
    saveAnalysisHistory?: boolean;
    darkMode?: boolean;
  }): Observable<any> {
    return this.http.put(`${this.apiUrl}/settings`, settings, { headers: this.authHeaders() });
  }

  // ── Analysis ────────────────────────────────
  /**
   * Uploads a skin photo and runs the real AI analysis (skin type + condition
   * detection via the backend's Hugging Face integration). The result is
   * persisted server-side and returned here for display.
   */
  analyzeSkin(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('photo', file);
    return this.http.post(`${this.apiUrl}/analysis/scan`, formData, {
      headers: new HttpHeaders({ Authorization: `Bearer ${this.getToken() ?? ''}` })
    });
  }

  saveAnalysis(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/analysis/save`, data, { headers: this.authHeaders() });
  }

  getAnalysisHistory(page = 1, limit = 10): Observable<any> {
    return this.http.get(`${this.apiUrl}/analysis/history?page=${page}&limit=${limit}`, { headers: this.authHeaders() });
  }

  // ── Local Storage ──────────────────────────
  saveToken(token: string, user: any): void {
    if (isPlatformBrowser(this.platformId)) {
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));
    }
  }

  getToken(): string | null {
    return isPlatformBrowser(this.platformId) ? localStorage.getItem('token') : null;
  }

  getUser(): any {
    if (isPlatformBrowser(this.platformId)) {
      const user = localStorage.getItem('user');
      return user ? JSON.parse(user) : null;
    }
    return null;
  }

  /** Update only the fields you pass (name, phone, etc.) inside the cached user */
  updateLocalUser(partial: any): void {
    if (isPlatformBrowser(this.platformId)) {
      const existing = this.getUser() || {};
      localStorage.setItem('user', JSON.stringify({ ...existing, ...partial }));
    }
  }

  logout(): void {
    if (isPlatformBrowser(this.platformId)) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
  }
}