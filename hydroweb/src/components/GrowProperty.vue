<template>
  <div
    :class="{
      level: true,
      'is-mobile':true,
      'mb-1': true, 'p-2': true,
      notification: true,
      'has-text-dark': true,
  }"
  >
  <!-- :style="getBackgroundStyle('#e5e5e5')" -->

    <div class="level-left">
      <div class="level-item">
        <div class="ml-1">
          <p>{{ property.name }}</p>
          <p style="font-size: 0.6em;">{{ property.description }}</p>
        </div>
      </div>
    </div>

    <div class="level-right pr-0 mr-0">
      <div class="level-item">
        <div v-if="!property.sensor">

          <div :class="{dropdown: true, 'is-right': true, 'is-active': assigning}">
            <!-- trigger -->
            <div class="dropdown-trigger">
              <button
                class="button is-small is-rounded"
                v-on:click="assigning = !assigning"
              >
                <span class="icon is-small">
                  <i class="fas fa-hammer"></i>
                </span>
                <span class="mr-2">assign</span>
                <i class="fas fa-angle-down" aria-hidden="true"></i>
              </button>
            </div>
            <!-- menu -->
            <div class="dropdown-menu">
              <div class="dropdown-content">
                <a
                  v-for="(sensor, index) in device.sensors"
                  :key="'assign_sensor_' + device.id + index"
                  v-on:click="sensorAssign(sensor.id)"
                  href="#" class="dropdown-item"
                > {{ sensor.description }}</a>
              </div>
            </div>
          </div>

        </div>
        <div v-else class="level is-mobile">
          <p class="mr-2">{{ property.sensor.last_value }} {{ property.sensor.unit }}</p>
          <span class="icon has-text-success">
            <i class="fas fa-check-circle"></i>
          </span>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import axios from 'axios';
import {baseURL} from "@/app.config";

export default {
  props: ['device', 'property'],

  data() {
    return {
      assigning: false,
    };
  },

  methods: {
    sensorAssign(sensorId) {
      const path = `${baseURL}/grow/systems/${this.device.id}/properties/${this.property.id}`;
      const options = {
        headers: { 'Content-Type': 'application/json' },
      };
      const data = {
        sensor_id: sensorId,
      };
      axios.post(path, data, options)
        .then(() => {
          this.assigning = false;
        })
        .catch(() => {
        });
    },
    sensorDelete() {
      // const path = `${baseURL}/devices/${this.device.id}/sensors/${id}`;
      // axios.delete(path);
    },

    getBackgroundStyle(colorHex) {
      var width = 100;
      if (this.property.sensor) {
        width = 50;
      }
      return `background-image: -webkit-linear-gradient(0deg, ${colorHex} ${width}%, #ffffff00 ${width + 80}%);`;    },
  },

};
</script>

<style>

</style>
