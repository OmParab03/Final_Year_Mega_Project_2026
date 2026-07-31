import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from './auth.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  ReactiveFormsModule,
  FormBuilder,
  FormGroup,
  Validators,
  AbstractControl
} from '@angular/forms';

@Component({
  selector: 'app-auth',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  templateUrl: './auth.html',
  styleUrls: ['./auth.css']
})
export class Auth {
  errorMessage: string = '';
  successMessage: string = '';
  isLoading: boolean = false;
  isSignIn: boolean = true;
  showPassword: boolean = false;
  showConfirmPassword: boolean = false;

  authForm: FormGroup;
  formType: 'signIn' | 'signUp' = 'signIn';

  constructor(
    private authService: AuthService,
    private router: Router,
    private fb: FormBuilder
  ) {
    this.authForm = this.fb.group({});
    this.initializeForm();
  }

  // ==================== FORM INIT ====================
  initializeForm(): void {
    if (this.formType === 'signIn') {
      this.authForm = this.fb.group({
        email: ['', [Validators.required, Validators.email]],
        password: ['', [Validators.required, Validators.minLength(6)]]
      });
    } else {
      this.authForm = this.fb.group(
        {
          name: ['', Validators.required],
          email: ['', [Validators.required, Validators.email]],
          password: ['', [Validators.required, Validators.minLength(6)]],
          confirmPassword: ['', Validators.required]
        },
        { validators: this.passwordMatchValidator }
      );
    }
  }

  passwordMatchValidator(form: AbstractControl) {
    const password = form.get('password')?.value;
    const confirmPassword = form.get('confirmPassword')?.value;
    return password === confirmPassword ? null : { mismatch: true };
  }

  // ==================== SWITCH FORMS ====================
  switchToSignIn(): void {
    if (this.isSignIn) return;
    this.isSignIn = true;
    this.formType = 'signIn';
    this.resetState();
    this.initializeForm();
  }

  switchToSignUp(): void {
    if (!this.isSignIn) return;
    this.isSignIn = false;
    this.formType = 'signUp';
    this.resetState();
    this.initializeForm();
  }

  switchForm(): void {
    this.isSignIn ? this.switchToSignUp() : this.switchToSignIn();
  }

  resetState(): void {
    this.errorMessage = '';
    this.successMessage = '';
    this.isLoading = false;
    this.showPassword = false;
    this.showConfirmPassword = false;
  }

  // ==================== PASSWORD STRENGTH ====================
  getPasswordStrength(): { width: string; color: string; label: string } {
    const password = this.authForm.get('password')?.value || '';
    const length = password.length;

    if (length === 0) {
      return { width: '0%', color: '#e5e7eb', label: '' };
    }
    if (length < 4) {
      return { width: '20%', color: '#ef4444', label: 'Very weak' };
    }
    if (length < 6) {
      return { width: '40%', color: '#f97316', label: 'Weak' };
    }

    let strength = 0;
    if (length >= 8) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;

    if (strength <= 1) {
      return { width: '50%', color: '#eab308', label: 'Fair' };
    } else if (strength === 2) {
      return { width: '70%', color: '#22c55e', label: 'Good' };
    } else {
      return { width: '100%', color: '#16a34a', label: 'Strong' };
    }
  }

  // ==================== SUBMIT ====================
  onSubmit(): void {
    if (this.authForm.invalid) {
      this.authForm.markAllAsTouched();
      this.errorMessage = 'Please fill in all fields correctly.';
      return;
    }

    this.errorMessage = '';
    this.successMessage = '';
    this.isLoading = true;

    const formData = this.authForm.value;

    if (this.formType === 'signIn') {
      this.authService
        .signin({
          email: formData['email'],
          password: formData['password']
        })
        .subscribe({
          next: (res: any) => this.onSuccess(res),
          error: (err: any) => this.onError(err)
        });
    } else {
      this.authService
        .signup({
          name: formData['name'],
          email: formData['email'],
          password: formData['password']
        })
        .subscribe({
          next: (res: any) => this.onSuccess(res),
          error: (err: any) => this.onError(err)
        });
    }
  }

  // ==================== HANDLERS ====================
  onSuccess(res: any): void {
    this.isLoading = false;

    if (this.formType === 'signUp') {
      this.successMessage = 'Account created! Signing you in...';
    }

    this.authService.saveToken(res.token, res.user);

    const delay = this.formType === 'signUp' ? 1000 : 300;
    setTimeout(() => {
      this.router.navigate(['/dashboard']);
    }, delay);
  }

  onError(err: any): void {
    this.isLoading = false;
    const action = this.formType === 'signIn' ? 'Sign in' : 'Sign up';
    this.errorMessage =
      err.error?.message || `${action} failed. Please try again.`;

    setTimeout(() => {
      this.errorMessage = '';
    }, 5000);
  }

  // ==================== FORM GETTERS ====================
  get nameControl(): AbstractControl | null {
    return this.authForm.get('name');
  }

  get emailControl(): AbstractControl | null {
    return this.authForm.get('email');
  }

  get passwordControl(): AbstractControl | null {
    return this.authForm.get('password');
  }

  get confirmPasswordControl(): AbstractControl | null {
    return this.authForm.get('confirmPassword');
  }
}