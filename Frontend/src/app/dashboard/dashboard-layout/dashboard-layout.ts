import { Component, OnInit, PLATFORM_ID, inject } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { SidebarComponent } from '../sidebar/sidebar';
import { TopbarComponent } from '../topbar/topbar';
import { AuthService } from '../../auth/auth.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-dashboard-layout',
  standalone: true,
  imports: [CommonModule, RouterOutlet, SidebarComponent, TopbarComponent],
  templateUrl: './dashboard-layout.html',
  styleUrl: './dashboard-layout.css'
})
export class DashboardLayoutComponent implements OnInit {
  user: any = null;
  loading: boolean = true;
  errorMessage: string = '';
  sidebarCollapsed: boolean = false;

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

  toggleSidebar() {
    this.sidebarCollapsed = !this.sidebarCollapsed;
  }

  getGreeting(): string {
    const hour = new Date().getHours();
    if (hour < 12) return 'Morning';
    if (hour < 17) return 'Afternoon';
    return 'Evening';
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/']);
  }
}