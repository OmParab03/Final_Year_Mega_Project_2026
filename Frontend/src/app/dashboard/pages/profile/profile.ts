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
  editMode: boolean = false;
  successMessage: string = '';
  errorMessage: string = '';

  // Personal Info
  fullName: string = '';
  dob: string = '';
  allergies: string = '';

  // Skin Type Options — the only classes the classifier model predicts
  skinTypes = [
    'Dry',
    'Oily',
    'Combination'
  ];
  selectedSkinType: string = '';

  // Skin Condition Options — the only classes the condition model predicts
  skinConditions = [
    'None / Maintenance',
    'Acne',
    'Redness',
    'Pigmentation'
  ];
  selectedCondition: string = 'None / Maintenance';

  // Set once a real scan result is loaded, so the UI can say where these values came from
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
        setTimeout(() => {
          this.errorMessage = '';
          this.cdr.markForCheck();
        }, 3000);
      }
    });
  }

  /** Pulls the most recent skin scan and prefills the Skin Type / Condition sections with it. */
  loadLatestAnalysis() {
    this.authService.getAnalysisHistory(1, 1).subscribe({
      next: (res: any) => {
        const latest = res.history?.[0];
        if (latest) {
          this.hasRealAnalysis = true;
          this.lastAnalyzedDate = new Date(latest.createdAt).toLocaleDateString();

          if (latest.skinType) {
            this.selectedSkinType = this.matchSkinType(latest.skinType);
          }

          const conditions = latest.conditions || [];
          this.selectedCondition = conditions.length > 0
            ? this.matchCondition(conditions[0].label)
            : 'None / Maintenance';
        }
        this.cdr.markForCheck();
      },
      error: () => {
        // No scan yet, or history couldn't load — keep defaults, not worth surfacing an error here
      }
    });
  }

  private matchSkinType(rawLabel: string): string {
    const match = this.skinTypes.find(
      (t) => t.toLowerCase() === rawLabel.toLowerCase()
    );
    return match || rawLabel;
  }

  private matchCondition(rawLabel: string): string {
    const match = this.skinConditions.find(
      (c) => c.toLowerCase() === rawLabel.toLowerCase()
    );
    return match || rawLabel; // shown as free text if it doesn't match a known option
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
    this.cdr.markForCheck();
    setTimeout(() => {
      this.successMessage = '';
      this.cdr.markForCheck();
    }, 3000);
  }

  analyzeWithAI(type: string) {
    this.router.navigate(['/dashboard/skin-analysis']);
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/']);
  }
}
