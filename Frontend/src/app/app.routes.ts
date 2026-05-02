import { Routes } from '@angular/router';
import { Auth } from './auth/auth';
import { Dashboard } from './dashboard/dashboard';

export const routes: Routes = [
  { path: '', component: Auth },
  { path: 'dashboard', component: Dashboard },
  { path: '**', redirectTo: '' }
];