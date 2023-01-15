// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
// import Vue from 'vue'
// import App from './App'
// import router from './router'

// Vue.config.productionTip = false


// new Vue({
//   el: '#app',
//   router,
//   components: { App },
//   template: '<App/>'
// })

import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import PrimeVue from 'primevue/config';
import Dialog from 'primevue/dialog';
import InputText from 'primevue/inputtext';
import SplitButton from 'primevue/splitbutton';
import InputMask from 'primevue/inputmask';
import Button from 'primevue/button';
import Card from 'primevue/card';
import Accordion from 'primevue/accordion';
import AccordionTab from 'primevue/accordiontab';

import "primevue/resources/themes/saga-blue/theme.css"; //theme
import "primevue/resources/primevue.min.css"; //core CSS
import "primeicons/primeicons.css"; //icons
import "primeflex/primeflex.css";
import "video.js/dist/video-js.min.css";
import "video.js/dist/video.min.js";
// import BootstrapVue3 from 'bootstrap-vue-3';
// import 'bootstrap/dist/css/bootstrap.css'
// import 'bootstrap-vue-3/dist/bootstrap-vue-3.css'

const app = createApp(App);
app.use(router);
// app.use(BootstrapVue3)
app.use(PrimeVue, {ripple:true});
app.mount('#app');

app.component('Dialog', Dialog);
app.component('InputText', InputText);
app.component('InputMask', InputMask);
app.component('SplitButton', SplitButton);
app.component('Button', Button);
app.component('Card', Card);
app.component('Accordion', Accordion);
app.component('AccordionTab', AccordionTab);
app.config.globalProperties.url = "https://a1bf6b7b-9360-4775-9380-d97808c01c0b.mock.pstmn.io";

