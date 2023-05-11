<template>
<div class="level">
  <div v-if="error">
    <span class="tag is-danger is-light my-2">{{ error }}</span>
  </div>
  <div v-else>
    <div v-if="control.input === 'bool'">
      <a v-on:click="controlAction" style="max-width: 3em"
        :class="{
          button: true,
          'ml-4': true,
          'is-success': control.value,
          'is-warning': !control.value,
          'is-loading': loading
          }">{{ control.value ? 'on' : 'off' }}</a>
    </div>

    <!-- INT -->
    <div v-else-if="control.input === 'int' || control.input === 'float'" class="level is-mobile">
      <div class="field has-addons">
        <p class="control">
          <input v-model="updated_control.value" type="number" style="max-width: 5em"
            :class="{
              input:true,
              'is-success': updated_control.value != control.value
            }">
        </p>
        <p class="control">
          <button v-on:click="controlAction" style="min-width: 3em" :class="{
            'button': true,
            'is-success': true,
            'is-loading': loading,
            'is-static': updated_control.value == control.value
          }">
            <span class="icon is-small">
              <i class="fas fa-paper-plane"></i>
            </span>
          </button>
        </p>
      </div>
    </div>
    <div v-else>
      <!-- others ? -->
      ????
    </div>
  </div>
</div>
</template>

<script>
import axios from 'axios';
import {baseURL} from "@/app.config";

export default {
  props: ['control', 'device'],

  data() {
    return {
      error: null,
      loading: false,
      updated_control: {
        control: this.control.name,
        value: this.control.value,
      },
    };
  },

  methods: {

    controlAction() {
      const path = `${baseURL}/devices/${this.device.id}/action`;
      const options = {
        headers: { 'Content-Type': 'application/json' },
      };
      this.loading = true;
      axios.post(path, this.updated_control, options)
        .then(() => {
          this.error = null;
        })
        .catch((err) => {
          this.error = err;
          console.log(err.response.data);
          setTimeout(() => { this.error = null; }, 5000);
        })
        .finally(() => {
          this.loading = false;
        });
    },

  },

};
</script>
