<template>
  <div id="app" class="mb-5">
    <nav class="navbar"
         role="navigation" aria-label="main navigation">
      <!-- logo -->
      <div class="navbar-brand">
        <a class="navbar-item" href="/">
          <img src="plant_ico.png">
        </a>
        <div class="navbar-item">
          <h5 class="title is-5">HYDRO-HUB</h5>
        </div>
      </div>
    </nav>

    <!-- DEVICES MENU NAV DROPDOWN -->
    <div v-if="devices.length > 0">
      <button id="button" v-on:click="togglePanel" class="button is-light is-fullwidth mt-2">
        <i class="fa fa-microchip"></i>
        <p class="ml-3">show all devices</p>
      </button>
    </div>
    <div class="overlay" v-if="panel_active">
        <button id="button" v-on:click="togglePanel" class="button is-light is-fullwidth">
          <i class="fa fa-microchip"></i>
          <p class="ml-3">show all devices</p>
        </button>
        <div v-if="devices.length > 0" class="p-1">
          <nav class="panel container">
            <a v-for="(device, d_index) in devices" :key="'d'+d_index"
              v-bind:class="{'is-active': isActive(device)}"
              v-on:click="makeActive(device)"
              class="panel-block"
              style="opacity: 1;"
            >
              <span class="panel-icon"><i v-bind:class="getFontAwesome(device)"></i></span>
              <p class="ml-2">{{ device.name }}</p>
            </a>
          </nav>
        </div>
        <!-- scan -->
        <div class="container mt-1 p-1">
          <button disabled v-on:click="postScan" :class="{
            button:true,
            'is-fullwidth':true,
            'is-outlined':true,
            'is-link':true,
            'is-loading':scan_loading
          }">
            <span class="icon is-small">
              <i class="fas fa-barcode"></i>
            </span>
            <span>Scan</span>
          </button>
        </div>

    </div>

    <!-- DEVICE CONTAINER -->
    <div v-if="active_device != null">
      <Device :device="active_device" @triggerRefresh="getDevice"></Device>
    </div>

    <!-- no devices -->
    <div v-if="devices.length < 1">
      <div class="container my-5 py-5 has-text-centered">
        <section class="hero is-medium">
          <div class="hero-body">
            <p class="title">No active devices</p>
            <p class="subtitle ml-5">
              Seems like you've got nothing connected...
            </p>
          </div>
        </section>
      </div>
        <!-- scan -->
        <div class="has-text-centered">
          <p class="subtitle is-6">
            <small>Try to rescan configured ports.</small>
          </p>
          <button v-on:click="postScan" :class="{
            button:true,
            'is-link':true,
            'is-outlined':true,
            'is-loading':scan_loading
          }" style="min-width: 9em;">
            <span class="icon is-small">
              <i class="fas fa-barcode"></i>
            </span>
            <span>Scan</span>
          </button>
        </div>
    </div>

  </div>
</template>

<script>
import axios from 'axios';
import Device from './components/Device.vue';
import { baseURL } from "@/app.config";

const INTERVAL_VALUE = 1000;

export default {
  components: {
    Device,
  },

  data() {
    return {
      devices: [],
      active_tab: 0,
      active_device: null,
      server_down: false,
      panel_active: false,
      interval_id: null,

      scan_loading: false,
    };
  },
  methods: {
    // server communication
    getDevices() {
      const path = `${baseURL}/devices`;
      console.log(`BASE URL: ${baseURL}`)
      axios.get(path)
        .then((res) => {
          if (res.data.length < 1) {
            this.devices = [];
            return;
          }
          this.devices = res.data;
          if (!this.active_device) {
            [this.active_device] = this.devices;
            this.active_tab = this.active_device.id;
            this.getDevice();
          }
        })
        .catch(() => {
          this.active_device = null;
          this.devices = [];
          this.stopInterval();
        });
    },
    getDevice() {
      if (this.active_device == null) {
        return;
      }
      const path = `${baseURL}/devices/${this.active_device.id}`;
      axios.get(path)
        .then((res) => {
          if (res.status !== 'success') {
            if (res.data) {
              this.active_device = res.data;
            }
          }
        })
        .catch(() => {
          this.active_device = null;
          this.getDevices();
        });
    },
    postScan() {
      const path = `${baseURL}/devices/scan`;
      this.scan_loading = true;
      axios.post(path)
        .finally(() => {
          this.scan_loading = false;
          this.getDevices();
        });
    },

    // periodic polling
    startInterval() {
      if (this.interval_id) {
        // stop if running...
        this.stopInterval();
      }
      this.interval_id = setInterval(() => {
        this.getDevice();
      }, INTERVAL_VALUE);
    },
    stopInterval() {
      clearInterval(this.interval_id);
      this.interval_id = null;
    },

    toggleInterval() {
      if (this.interval_id) {
        this.stopInterval();
      } else {
        this.startInterval();
      }
    },

    // active device
    isActive(dev) {
      return dev.id === this.active_tab;
    },
    makeActive(dev) {
      this.active_device = dev;
      this.getDevice();
      this.active_tab = dev.id;
      this.togglePanel();
    },
    getActiveDevice() {
      return this.devices[this.active_tab];
    },

    // panel shenanigans
    showPanel() {
      this.stopInterval();
      this.getDevices();
      this.panel_active = true;
      this.disableScroll();
    },
    closePanel() {
      this.startInterval();
      this.panel_active = false;
      this.enableScroll();
    },
    disableScroll() {
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
      window.onscroll = function () {
        window.scrollTo(scrollLeft, scrollTop);
      };
    },
    enableScroll() {
      window.onscroll = function () {};
    },
    togglePanel() {
      if (this.panel_active) {
        this.closePanel();
      } else {
        this.showPanel();
      }
    },

    // device icon
    getFontAwesome(device) {
      if (device.type === 'serial') {
        return 'fas fa-plug';
      }
      if (device.type === 'wifi') {
        return 'fas fa-wifi';
      }
      if (device.type === 'generic') {
        return 'fa fa-microchip';
      }
      return 'fas fa-question';
    },
  },
  created() {
    this.getDevices();
    this.startInterval();
  },
};

</script>
<style>
  #app {
    -webkit-user-select: none;
    -moz-user-select: none;
    -khtml-user-select: none;
    -webkit-touch-callout: none;
    -ms-user-select: none;
    user-select: none;
  }
  .dot {
    height: 1em;
    width: 1em;
    border-radius: 50%;
    display: inline-block;
  }
</style>
