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

    this.authService.getProfile(token).subscribe({
      next: (res: any) => {
        this.user = res;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'Session expired!';
        setTimeout(() => {
          this.authService.logout();
          this.router.navigate(['/']);
        }, 2000);
      }
    });
  }

  goToSkin(){
    this.router.navigate(['/skin-analysis']);
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/']);
  }
}