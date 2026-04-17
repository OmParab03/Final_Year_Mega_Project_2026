import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-auth',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './auth.html',
  styleUrl: './auth.css',
})
export class Auth {

  // Toggle between Sign In and Sign Up
  isSignIn: boolean = true;

  // Sign In Form Data
  signInData = {
    email: '',
    password: ''
  };

  // Sign Up Form Data
  signUpData = {
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  };

  // Switch to Sign In
  showSignIn() {
    this.isSignIn = true;
  }

  // Switch to Sign Up
  showSignUp() {
    this.isSignIn = false;
  }

  // Sign In Submit
  onSignIn() {
    console.log('Sign In Data:', this.signInData);
    alert(`Welcome! ${this.signInData.email}`);
  }

  // Sign Up Submit
  onSignUp() {
    if (this.signUpData.password !== this.signUpData.confirmPassword) {
      alert('Passwords do not match!');
      return;
    }
    console.log('Sign Up Data:', this.signUpData);
    alert(`Account Created for ${this.signUpData.name}`);
  }

}