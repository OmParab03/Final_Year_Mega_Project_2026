import { Component, ChangeDetectorRef, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../../auth/auth.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './home.html',
  styleUrl: './home.css'
})
export class HomeComponent implements OnInit {

  // Stats
  totalScans: number = 0;
  totalReports: number = 0;
  skinScore: number = 0;

  // Upload state
  previewUrl: string | null = null;
  selectedFile: File | null = null;
  isDragging: boolean = false;
  analyzing: boolean = false;
  errorMessage: string = '';

  // Product Analysis State
  productScanResult: any = null;
  userProfile: any = null;
  apiUrl = 'http://localhost:5000/api';

  // Recent history
  recentHistory: any[] = [];

  constructor(private router: Router, private cdr: ChangeDetectorRef, private authService: AuthService) {}

  ngOnInit() {
    this.loadStats();
  }

  loadStats() {
    // Placeholder - connect to your backend
    this.totalScans = 0;
    this.totalReports = 0;
    this.skinScore = 0;
    this.recentHistory = [];
  }

  // ==================== FILE UPLOAD ====================
  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      this.processFile(input.files[0]);
    }
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = true;
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
    if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
      this.processFile(event.dataTransfer.files[0]);
    }
  }

  processFile(file: File) {
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      this.errorMessage = 'Please upload a JPG, PNG, or WEBP image.';
      this.cdr.markForCheck();
      setTimeout(() => {
        this.errorMessage = '';
        this.cdr.markForCheck();
      }, 3000);
      return;
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      this.errorMessage = 'File size must be less than 10MB.';
      this.cdr.markForCheck();
      setTimeout(() => {
        this.errorMessage = '';
        this.cdr.markForCheck();
      }, 3000);
      return;
    }

    this.selectedFile = file;
    this.productScanResult = null; // Clear previous results
    const reader = new FileReader();
    reader.onload = () => {
      this.previewUrl = reader.result as string;
      // FileReader callbacks run outside Angular's change-detection scheduler
      // (this app uses zoneless CD), so the view won't refresh on its own here.
      this.cdr.markForCheck();
    };
    reader.readAsDataURL(file);
  }

  removeImage() {
    this.previewUrl = null;
    this.selectedFile = null;
    this.productScanResult = null;
  }

  analyzeImage() {
    if (!this.selectedFile) return;
    this.analyzing = true;
    this.cdr.markForCheck();

    const formData = new FormData();
    formData.append('photo', this.selectedFile);

    // Also load user profile for the report header
    fetch(`${this.apiUrl}/profile`, {
      headers: { 'Authorization': `Bearer ${this.authService.getToken()}` }
    }).then(r => r.json()).then(p => { this.userProfile = p; this.cdr.markForCheck(); }).catch(() => {});

    fetch(`${this.apiUrl}/product/scan`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.authService.getToken()}`
      },
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      this.analyzing = false;
      if (data.analysis) {
        this.productScanResult = data.analysis;
      } else {
        this.errorMessage = data.message || 'Product analysis failed';
        setTimeout(() => this.errorMessage = '', 3000);
      }
      this.cdr.markForCheck();
    })
    .catch(err => {
      this.analyzing = false;
      this.errorMessage = 'Failed to connect to server';
      this.cdr.markForCheck();
      setTimeout(() => {
        this.errorMessage = '';
        this.cdr.markForCheck();
      }, 3000);
    });
  }

  goToHistory() {
    this.router.navigate(['/dashboard/skin-analysis']);
  }
}
