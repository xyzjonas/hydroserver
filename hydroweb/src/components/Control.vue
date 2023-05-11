<template>
<div class="level box mb-2 is-mobile">
  <div v-if="!is_edit" class="level-left">
    <a v-on:click="toggleEdit" class="icon">
      <i class="fas fa-edit"></i>
    </a>
    <p class="ml-4">{{ control.description }}</p>
  </div>
  <!-- edit -->
  <div v-if="is_edit" class="level-left">
    <div class="field is-grouped">
      <div class="control m-0">
        <input v-model="edit_name" class="input" type="text">
      </div>
      <div class="control mx-1">
        <a v-on:click="controlEdit" class="button is-success is-outlined">
          <span class="icon is-small">
            <i class="fas fa-check"></i>
          </span>
        </a>
      </div>
      <div class="control">
        <a v-on:click="toggleEdit" class="button is-outlined">
          <span class="icon is-small">
            <i class="fas fa-times"></i>
          </span>
        </a>
      </div>
    </div>
  </div>
  <div class="level-right">
    <ControlHandle :control="control" :device="device"/>
  </div>
</div>
</template>

<script>
import axios from 'axios';
import { baseURL } from "@/app.config";
import ControlHandle from './ControlHandle.vue';

export default {
  props: ['control', 'device'],

  components: {
    ControlHandle,
  },

  data() {
    return {
      is_edit: false,
      edit_name: this.control.description,
      edit_error: null,

      options: {
        weekday: 'short',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric',
        second: 'numeric',
      },

      editTaskInterval_l: 20,
      editTaskInterval_r: 25,
      editTaskData: {
        meta: {
        },
      },
    };
  },

  methods: {
    controlAction() {
      const path = `${baseURL}/devices/${this.device.id}/action`;
      const options = {
        headers: { 'Content-Type': 'application/json' },
      };
      const data = { control: this.control.name };
      axios.post(path, data, options)
        .then(() => {
        });
    },
    controlEdit() {
      const path = `${baseURL}/devices/${this.device.id}/controls/${this.control.id}`;
      const options = {
        headers: { 'Content-Type': 'application/json' },
      };
      const data = {
        control: this.control.name,
        description: this.edit_name,
      };
      axios.post(path, data, options)
        .then(() => {
          this.edit_error = null;
          this.control.description = this.edit_name;
          this.is_edit = false;
        })
        .catch((err) => {
          this.edit_error = err.response.data;
        });
    },
    controlDelete(id) {
      const path = `${baseURL}/devices/${this.device.id}/controls/${id}`;
      axios.delete(path);
    },
    toggleEdit() {
      this.is_edit = !this.is_edit;
    },
  },
};
</script>

<style>

</style>
