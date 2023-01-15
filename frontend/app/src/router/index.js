
// import HelloWorld from '@/components/HelloWorld'
import Main from '@/pages/Main';
import Search from '@/pages/Search';
import Result from '@/pages/Result';

import { createRouter, createWebHistory } from 'vue-router';
const routes = [
  {
    path: '/',
    name: 'Main',
    component: Main
  },
  {
    path: '/search',
    name: 'Search',
    component: Search
  },
  {
    path: '/result',
    name: 'Result',
    component: Result
  }
]

const router = new createRouter({
  history: createWebHistory(), 
  routes: routes
});

export default router;