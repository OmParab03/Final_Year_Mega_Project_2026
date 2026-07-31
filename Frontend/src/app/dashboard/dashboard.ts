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

  // Stats (can be fetched from backend)
  totalScans: number = 0;
  totalReports: number = 0;
  skinScore: number = 0;

  // Recent history
  recentHistory: any[] = [];

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
}