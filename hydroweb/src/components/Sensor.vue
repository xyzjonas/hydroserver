<template>
<div>
  <div class="level box mb-2 is-mobile">
    <div v-if="!is_edit" class="level-left">
      <a v-on:click="toggleEdit" class="icon">
        <i class="fas fa-edit"></i>
      </a>
      <p class="ml-4">{{ sensor.description }}</p>
    </div>
    <!-- edit -->
    <div v-else class="level-left">
      <div class="control mr-0">
        <input v-model="edit_name" class="input" type="text">
      </div>
      <div class="control mx-1">
        <button v-on:click="sensorEdit" class="button is-success is-outlined">
          <span class="icon is-small">
            <i class="fas fa-check"></i>
          </span>
        </button>
      </div>
      <div class="control">
        <button v-on:click="toggleEdit" class="button is-outlined">
          <span class="icon is-small">
            <i class="fas fa-times"></i>
          </span>
        </button>
      </div>
    </div>
  <div class="level-right">
    <p><strong>{{ sensor.last_value }}</strong> {{ sensor.unit }}</p>
  </div>

  </div>
</div>
</template>

<script>
import axios from 'axios';
import {baseURL} from "@/app.config";

export default {
  props: ['sensor', 'device'],

  data() {
    return {
      is_edit: false,
      edit_name: this.sensor.description,
      edit_error: null,
    };
  },

  methods: {
    sensorEdit() {
      const path = `${baseURL}/devices/${this.device.id}/sensors/${this.sensor.id}`;
      const options = {
        headers: { 'Content-Type': 'application/json' },
      };
      const data = {
        description: this.edit_name,
      };
      axios.post(path, data, options)
        .then(() => {
          this.edit_error = null;
          this.sensor.description = this.edit_name;
          this.is_edit = false;
        })
        .catch((err) => {
          // todo: show error
          this.edit_error = err.response.data;
        });
    },
    sensorDelete(id) {
      const path = `${baseURL}/devices/${this.device.id}/sensors/${id}`;
      axios.delete(path);
    },
    toggleEdit() {
      this.is_edit = !this.is_edit;
    },
  },
  created() {
  },
};
</script>

<style>

</style>
