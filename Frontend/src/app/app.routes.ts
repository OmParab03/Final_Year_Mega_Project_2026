import { Routes } from '@angular/router';
import { Auth } from './auth/auth';
import { Dashboard } from './dashboard/dashboard';
import { SkinAnalysis } from './dashboard/pages/skin-analysis/skin-analysis';

export const routes: Routes = [
  { path: '', component: Auth },
  { path: 'dashboard', component: Dashboard },
  { path: 'skin-analysis', component: SkinAnalysis },
  { path: '**', redirectTo: '' }
];