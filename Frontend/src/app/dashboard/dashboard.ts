import { Component, OnInit, PLATFORM_ID, inject } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../auth/auth.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css'
})
export class Dashboard implements OnInit {
  user: any = null;
  loading: boolean = true;
  errorMessage: string = '';
  activeTab: string = 'dashboard';
  sidebarCollapsed: boolean = true;

  // Upload state
  previewUrl: string | null = null;
  selectedFile: File | null = null;
  isDragging: boolean = false;
  analyzing: boolean = false;
  analyzingProduct: boolean = false;
  
  // Product Analysis State
  productScanResult: any = null;
  productPreviewUrl: string | null = null;
  productSelectedFile: File | null = null;
  productHistory: any[] = [];

  // Stats (can be fetched from backend)
  totalScans: number = 0;
  totalReports: number = 0;
  skinScore: number = 0;

  // Recent history
  recentHistory: any[] = [];
  
  apiUrl = 'http://localhost:5000/api';

  private platformId = inject(PLATFORM_ID);

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit() {
    if (!isPlatformBrowser(this.platformId)) {
      this.loading = false;
      return;
    }

    // Handle sidebar for mobile
    if (window.innerWidth <= 768) {
      this.sidebarCollapsed = true;
    } else {
      this.sidebarCollapsed = false;
    }

    const token = this.authService.getToken();
    if (!token) {
      this.loading = false;
      this.router.navigate(['/']);
      return;
    }

    const savedUser = this.authService.getUser();
    if (savedUser) {
      this.user = savedUser;
      this.loading = false;
    }

    this.authService.getProfile().subscribe({
      next: (res: any) => {
        this.user = res;
        this.loading = false;
        this.loadUserStats();
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'Session expired. Redirecting to login...';
        setTimeout(() => {
          this.authService.logout();
          this.router.navigate(['/']);
        }, 2000);
      }
    });
  }

  getGreeting(): string {
    const hour = new Date().getHours();
    if (hour < 12) return 'Morning';
    if (hour < 17) return 'Afternoon';
    return 'Evening';
  }

  loadUserStats() {
    // Fetch Skin History
    fetch(`${this.apiUrl}/analysis/history?limit=5`, {
      headers: { 'Authorization': `Bearer ${this.authService.getToken()}` }
    })
    .then(res => res.json())
    .then(data => {
      this.recentHistory = data.history || [];
      this.totalScans = data.total || 0;
    });

    // Fetch Product History
    fetch(`${this.apiUrl}/product/history?limit=10`, {
      headers: { 'Authorization': `Bearer ${this.authService.getToken()}` }
    })
    .then(res => res.json())
    .then(data => {
      this.productHistory = data.history || [];
    });
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
      setTimeout(() => this.errorMessage = '', 3000);
      return;
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      this.errorMessage = 'File size must be less than 10MB.';
      setTimeout(() => this.errorMessage = '', 3000);
      return;
    }

    this.selectedFile = file;
    const reader = new FileReader();
    reader.onload = () => {
      this.previewUrl = reader.result as string;
    };
    reader.readAsDataURL(file);
  }

  removeImage() {
    this.previewUrl = null;
    this.selectedFile = null;
  }

  analyzeImage() {
    if (!this.selectedFile) return;

    this.analyzing = true;

    // Navigate to skin analysis page with file data
    // You can use a shared service to pass the file
    setTimeout(() => {
      this.analyzing = false;
      this.router.navigate(['/skin-analysis']);
    }, 1500);
  }

  goToSkin() {
    this.router.navigate(['/skin-analysis']);
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/']);
  }

  // ==================== PRODUCT SCAN ====================
  onProductFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      this.processProductFile(input.files[0]);
    }
  }

  onProductDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;

    if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
      this.processProductFile(event.dataTransfer.files[0]);
    }
  }

  processProductFile(file: File) {
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      this.errorMessage = 'Please upload a JPG, PNG, or WEBP image.';
      setTimeout(() => this.errorMessage = '', 3000);
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      this.errorMessage = 'File size must be less than 10MB.';
      setTimeout(() => this.errorMessage = '', 3000);
      return;
    }

    this.productSelectedFile = file;
    const reader = new FileReader();
    reader.onload = () => {
      this.productPreviewUrl = reader.result as string;
      this.productScanResult = null; // reset previous result
    };
    reader.readAsDataURL(file);
  }

  removeProductImage() {
    this.productPreviewUrl = null;
    this.productSelectedFile = null;
    this.productScanResult = null;
  }

  analyzeProductImage() {
    if (!this.productSelectedFile) return;

    this.analyzingProduct = true;
    const formData = new FormData();
    formData.append('photo', this.productSelectedFile);

    fetch(`${this.apiUrl}/product/scan`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.authService.getToken()}`
      },
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      this.analyzingProduct = false;
      if (data.analysis) {
        this.productScanResult = data.analysis;
        this.loadUserStats(); // refresh history
      } else {
        this.errorMessage = data.message || 'Product analysis failed';
        setTimeout(() => this.errorMessage = '', 3000);
      }
    })
    .catch(err => {
      this.analyzingProduct = false;
      this.errorMessage = 'Failed to connect to server';
      setTimeout(() => this.errorMessage = '', 3000);
    });
  }
}