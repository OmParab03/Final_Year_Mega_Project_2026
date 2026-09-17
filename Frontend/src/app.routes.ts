import { Routes } from '@angular/router';
import { Auth } from './app/auth/auth';
import { Dashboard } from './app/dashboard/dashboard';

export const routes: Routes = [
  { path: '', component: Auth },
  { path: 'dashboard', component: Dashboard },
  { path: '**', redirectTo: '' }
];
