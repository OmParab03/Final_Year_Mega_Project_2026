import { Component, ChangeDetectorRef, OnInit } from '@angular/core';
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
  saving: boolean = false;
  editMode: boolean = false;
  successMessage: string = '';
  errorMessage: string = '';

  apiUrl = 'http://localhost:5000/api';

  // Personal Info
  fullName: string = '';
  phone: string = '';
  dob: string = '';
  allergies: string = '';  // comma-separated string for UI

  // Skin Type Options
  skinTypes = ['Dry', 'Oily', 'Combination'];
  selectedSkinType: string = '';

  // Skin Condition Options
  skinConditions = ['None / Maintenance', 'Acne', 'Redness', 'Pigmentation'];
  selectedCondition: string = 'None / Maintenance';

  // Read-only display: date of last AI skin scan
  lastAnalyzedDate: string | null = null;
  hasRealAnalysis: boolean = false;

  constructor(
    private authService: AuthService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit() {
    this.loadProfile();
    this.loadLatestAnalysis();
  }

  loadProfile() {
    this.loading = true;

    const savedUser = this.authService.getUser();
    if (savedUser) {
      this.user = savedUser;
      this.fillForm(savedUser);
      this.loading = false;
      this.cdr.markForCheck();
    }

    this.authService.getProfile().subscribe({
      next: (res: any) => {
        this.user = res;
        this.fillForm(res);
        this.loading = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'Failed to load profile.';
        this.cdr.markForCheck();
        setTimeout(() => { this.errorMessage = ''; this.cdr.markForCheck(); }, 3000);
      }
    });
  }

  /** Pulls the most recent skin scan and prefills Skin Type / Condition if not set in profile. */
  loadLatestAnalysis() {
    this.authService.getAnalysisHistory(1, 1).subscribe({
      next: (res: any) => {
        const latest = res.history?.[0];
        if (latest) {
          this.hasRealAnalysis = true;
          this.lastAnalyzedDate = new Date(latest.createdAt).toLocaleDateString();
          // Only prefill from scan if user hasn't set these manually
          if (!this.selectedSkinType && latest.skinType) {
            this.selectedSkinType = this.matchSkinType(latest.skinType);
          }
          if (this.selectedCondition === 'None / Maintenance') {
            const conditions = latest.conditions || [];
            this.selectedCondition = conditions.length > 0
              ? this.matchCondition(conditions[0].label)
              : 'None / Maintenance';
          }
        }
        this.cdr.markForCheck();
      },
      error: () => {} // No scan yet — silently skip
    });
  }

  private matchSkinType(rawLabel: string): string {
    return this.skinTypes.find(t => t.toLowerCase() === rawLabel.toLowerCase()) || rawLabel;
  }

  private matchCondition(rawLabel: string): string {
    return this.skinConditions.find(c => c.toLowerCase() === rawLabel.toLowerCase()) || rawLabel;
  }

  fillForm(user: any) {
    this.fullName  = user?.name || '';
    this.phone     = user?.phone || '';
    this.dob       = user?.dob || '';
    // allergies comes from DB as array — convert to comma string for the input
    const rawAllergies = user?.allergies;
    if (Array.isArray(rawAllergies)) {
      this.allergies = rawAllergies.join(', ');
    } else {
      this.allergies = rawAllergies || '';
    }
    this.selectedSkinType  = user?.skin_type  || '';
    this.selectedCondition = user?.skin_condition || 'None / Maintenance';
  }

  // Calculate age from DOB
  get calculatedAge(): number | null {
    if (!this.dob) return null;
    const birthDate = new Date(this.dob);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const m = today.getMonth() - birthDate.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) age--;
    return age >= 0 ? age : null;
  }

  toggleEdit() {
    if (this.editMode) {
      // Cancel — reload from server to discard unsaved changes
      this.fillForm(this.user);
    }
    this.editMode = !this.editMode;
  }

  saveChanges() {
    this.saving = true;
    const token = this.authService.getToken();

    const payload: any = {
      name:           this.fullName.trim(),
      phone:          this.phone.trim(),
      dob:            this.dob,
      allergies:      this.allergies,   // backend handles comma-string → array
      skin_type:      this.selectedSkinType,
      skin_condition: this.selectedCondition,
    };

    fetch(`${this.apiUrl}/profile`, {
      method:  'PUT',
      headers: {
        'Content-Type':  'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
      this.saving = false;
      if (data.user) {
        this.user = data.user;
        this.fillForm(data.user);
        this.successMessage = 'Profile saved to database successfully!';
        this.editMode = false;
      } else {
        this.errorMessage = data.message || 'Failed to save profile.';
      }
      this.cdr.markForCheck();
      setTimeout(() => { this.successMessage = ''; this.errorMessage = ''; this.cdr.markForCheck(); }, 3000);
    })
    .catch(() => {
      this.saving = false;
      this.errorMessage = 'Connection error. Could not save profile.';
      this.cdr.markForCheck();
      setTimeout(() => { this.errorMessage = ''; this.cdr.markForCheck(); }, 3000);
    });
  }

  analyzeWithAI(type: string) {
    this.router.navigate(['/dashboard/skin-analysis']);
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/']);
  }
}

