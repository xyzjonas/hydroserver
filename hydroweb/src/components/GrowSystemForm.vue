<template>
<div class="px-3 mt-2">
    <div class="field">
    <div class="control">
        <input v-model="system.name" class="input" type="text" placeholder="name">
    </div>
    </div>

    <div :class="{dropdown: true, 'is-active': dropdownActive}">
    <div class="dropdown-trigger">
        <button v-on:click="dropdown()" :class="{button: true, 'is-is-loading': properties_is_loading}">
        <span>Add a grow property</span>
        <span class="icon is-small">
            <i class="fas fa-angle-down" aria-hidden="true"></i>
        </span>
        </button>
    </div>
    <div class="dropdown-menu">
        <div class="dropdown-content">
        <a v-for="(prop, index) in availableProperties" :key="index + 'systemprop'" 
           v-on:click="selectProperty(prop)"
           class="dropdown-item">
            {{ prop.name }}
        </a>
        </div>
    </div>
    </div>

    <div class="mt-2 mb-5">
        <span v-for="(prop, index) in system.properties" :key="index + 'selpropsyst'"
        class="tag is-medium pl-5 pr-4 m-1">
        {{ prop.name }}
        <button v-on:click="deselectProperty(prop)" class="delete is-small ml-4"></button>
        </span>
    </div>


    <div class="field is-grouped mt-2">
    <div class="control">
        <button v-on:click="post()" class="button is-success is-outlined">Submit</button>
    </div>
    <div class="control">
        <button v-on:click="cancel()" class="button">Cancel</button>
    </div>
    </div>

    <small class="has-text-danger">{{postError}}</small>
</div>
</template>

<script>
import axios from 'axios';
import {baseURL} from "@/app.config";

export default {

  props: ["system_in"],
  
  data() {
      return {
          dropdownActive: false,
          properties_is_loading: false,

          postError: null,
          system: {
              name: "",
              properties: [],
          },

          availableProperties: [],
      }
  },

    methods: {
        
        selectProperty(prop) {
            this.system.properties.push(prop);
            this.dropdownActive = false;
        },

        deselectProperty(prop) {
            this.system.properties.pop(prop);
        },

        dropdown() {
            if (this.dropdownActive) {
                this.dropdownActive = false;
                return;
            }
            const path = `${baseURL}/grow/properties`;
            this.properties_is_loading = true;
            axios.get(path)
            .then(res => {
                this.availableProperties = res.data.filter(prop => {
                    return !this.system.properties.map(p => p.name).includes(prop.name);
                });
                this.dropdownActive = true;
            })
            .catch(err => {
                this.properties_error = err;
            })
            .finally(() => {
                this.properties_is_loading = false;
            });
            
        },

        cancel() {
          this.$emit('cancel');
        },

        post() {
            var path = null;
            if (this.system.id) {
                path = `${baseURL}/grow/systems/${this.system.id}`;
            } else {
                // new system is being created
                path = `${baseURL}/grow/systems/new`;
            }
            const options = {headers: { 'Content-Type': 'application/json' }};
            axios.post(path, this.system, options)
                 .then(() => {
                     this.postError = null;
                     this.$emit('posted');
                    })
                 .catch(err => {this.postError = `${err.response.data}`;})
        },

        getGrowProperties() {
            const path = `${baseURL}/grow/properties`;
            this.properties_is_loading = true;
            axios.get(path)
            .then(res => {
                this.growProperties = res.data;
            })
            .catch(err => {
                this.properties_error = err;
            })
            .finally(() => {
                this.properties_is_loading = false;
            });
        },

    },

    created() {
        if (this.system_in) {
            this.system = {
                ...this.system_in
            };
        }
    }
};
</script>

<style>

</style>
