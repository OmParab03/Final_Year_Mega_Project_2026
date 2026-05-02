import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from './auth.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-auth',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './auth.html',
  styleUrls: ['./auth.css']
})
export class Auth {

  errorMessage: string = '';
  successMessage: string = '';
  isLoading: boolean = false;

  isSignIn: boolean = true;

  signInData = {
    email: '',
    password: ''
  };

  signUpData = {
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  };

  constructor(
    private authService: AuthService,
    private router: Router
  ) {
    // Removed: Don't check localStorage in constructor (SSR issue)
  }

  showSignIn() {
    this.isSignIn = true;
    this.errorMessage = '';
    this.successMessage = '';
    this.isLoading = false;
  }

  showSignUp() {
    this.isSignIn = false;
    this.errorMessage = '';
    this.successMessage = '';
    this.isLoading = false;
  }

  onSignIn() {
    this.errorMessage = '';
    this.successMessage = '';

    if (!this.signInData.email || !this.signInData.password) {
      this.errorMessage = 'Please fill in all fields!';
      return;
    }

    this.isLoading = true;

    this.authService.signin(this.signInData).subscribe({
      next: (res: any) => {
        console.log('Login Success:', res);
        this.isLoading = false;
        this.authService.saveToken(res.token, res.user);
        this.router.navigate(['/dashboard']);
      },
      error: (err: any) => {
        console.log('Login Error:', err);
        this.isLoading = false;
        this.errorMessage = err.error?.message || 'Login Failed!';
      }
    });
  }

  onSignUp() {
    this.errorMessage = '';
    this.successMessage = '';

    if (!this.signUpData.name || !this.signUpData.email ||
        !this.signUpData.password || !this.signUpData.confirmPassword) {
      this.errorMessage = 'Please fill in all fields!';
      return;
    }

    if (this.signUpData.password !== this.signUpData.confirmPassword) {
      this.errorMessage = 'Passwords do not match!';
      return;
    }

    if (this.signUpData.password.length < 6) {
      this.errorMessage = 'Password must be at least 6 characters!';
      return;
    }

    this.isLoading = true;

    this.authService.signup(this.signUpData).subscribe({
      next: (res: any) => {
        console.log('Signup Success:', res);
        this.isLoading = false;
        this.successMessage = 'Account created successfully!';
        this.authService.saveToken(res.token, res.user);
        this.router.navigate(['/dashboard']);
      },
      error: (err: any) => {
        console.log('Signup Error:', err);
        this.isLoading = false;
        this.errorMessage = err.error?.message || 'Signup Failed!';
      }
    });
  }
}