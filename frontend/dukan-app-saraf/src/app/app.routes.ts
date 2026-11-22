import { Routes } from '@angular/router';
import { LoginComponent } from './login/login';
import { CreateUserComponent } from './create-user/create-user';
import { DashboardComponent } from './dashboard/dashboard';

export const routes: Routes = [
  { path: '',             redirectTo: 'login', pathMatch: 'full' },
  { path: 'login',        component: LoginComponent },
  { path: 'create-user',  component: CreateUserComponent },
  { path: 'dashboard',    component: DashboardComponent },
];
