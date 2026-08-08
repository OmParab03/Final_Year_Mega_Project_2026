import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../auth/auth.service';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './profile.html',
  styleUrl: './profile.css'
})
export class ProfileComponent implements OnInit {
  user: any = null;
  loading: boolean = true;
  editMode: boolean = false;
  successMessage: string = '';
  errorMessage: string = '';

  // Personal Info
  fullName: string = '';
  dob: string = '';
  allergies: string = '';

  // Skin Type Options
  skinTypes = [
    'Normal',
    'Dry',
    'Combination',
    'Oily',
    'Sensitive'
  ];
  selectedSkinType: string = 'Oily';

  // Skin Condition Options
  skinConditions = [
    'None / Maintenance',
    'Acne',
    'Pigmentation',
    'Redness / Rosacea',
    'Aging / Wrinkles',
    'Dehydration'
  ];
  selectedCondition: string = 'None / Maintenance';

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit() {
    this.loadProfile();
  }

  loadProfile() {
    this.loading = true;

    const savedUser = this.authService.getUser();
    if (savedUser) {
      this.user = savedUser;
      this.fillForm(savedUser);
      this.loading = false;
    }

    this.authService.getProfile().subscribe({
      next: (res: any) => {
        this.user = res;
        this.fillForm(res);
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'Failed to load profile.';
        setTimeout(() => this.errorMessage = '', 3000);
      }
    });
  }

  fillForm(user: any) {
    this.fullName = user?.name || '';
    this.dob = user?.dob || '';
    this.allergies = user?.allergies || '';
  }

  // ✅ Calculate age from DOB
  get calculatedAge(): number | null {
    if (!this.dob) return null;

    const birthDate = new Date(this.dob);
    const today = new Date();

    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();

    // If birthday hasn't happened yet this year, subtract 1
    if (
      monthDiff < 0 ||
      (monthDiff === 0 && today.getDate() < birthDate.getDate())
    ) {
      age--;
    }

    return age >= 0 ? age : null;
  }

  toggleEdit() {
    this.editMode = !this.editMode;
  }

  saveChanges() {
    // Placeholder - connect to backend
    this.successMessage = 'Profile updated successfully!';
    this.editMode = false;
    setTimeout(() => this.successMessage = '', 3000);
  }

  analyzeWithAI(type: string) {
    this.router.navigate(['/dashboard/skin-analysis']);
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/']);
  }
}