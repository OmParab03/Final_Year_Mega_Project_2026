import { Routes } from '@angular/router';
import { Auth } from './auth/auth';
import { DashboardLayoutComponent } from './dashboard/dashboard-layout/dashboard-layout';
import { HomeComponent } from './dashboard/pages/home/home';
import { HistoryComponent } from './dashboard/pages/history/history';
import { SkinAnalysis } from './dashboard/pages/skin-analysis/skin-analysis';
import { ProfileComponent } from './dashboard/pages/profile/profile';
import { SettingsComponent } from './dashboard/pages/settings/settings';

export const routes: Routes = [
  { path: '', component: Auth },
  {
    path: 'dashboard',
    component: DashboardLayoutComponent,
    children: [
      { path: '', component: HomeComponent }, // /dashboard loads the main stats & upload
      { path: 'history', component: HistoryComponent }, // /dashboard/history
      { path: 'skin-analysis', component: SkinAnalysis }, // /dashboard/skin-analysis
      { path: 'profile', component: ProfileComponent }, // /dashboard/profile
      { path: 'settings', component: SettingsComponent } // /dashboard/settings
    ]
  },
  { path: '**', redirectTo: '' }
];