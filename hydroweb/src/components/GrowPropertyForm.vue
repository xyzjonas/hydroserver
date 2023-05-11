<template>
<div class="px-3 mt-2">
    <div class="field">
    <div class="control">
        <input v-model="property.name" class="input" type="text" placeholder="name">
    </div>
    </div>

    <div class="field mb-0">
    <div class="control">
        <input v-model="property.description" class="input" type="text" placeholder="description">
    </div>
    </div>
    <small class="has-text-danger">{{postError}}</small>
    <div class="field is-grouped mt-2">
    <div class="control">
        <button v-on:click="post()" class="button is-success is-outlined">Submit</button>
    </div>
    <div class="control">
        <button v-on:click="cancel()" class="button">Cancel</button>
    </div>
    </div>
</div>
</template>

<script>
import axios from 'axios';
import {baseURL} from "@/app.config";

export default {

  props: ["prop_in"],
  
  data() {
      return {
          postError: null,
          property: {
              name: "",
              description: "",
          },
      }
  },

    methods: {

        cancel() {
          this.$emit('cancel');
        },

        post() {
            var path = null;
            if (this.property.id) {
                path = `${baseURL}/grow/properties/${this.property.id}`;
            } else {
                // new property is being created
                path = `${baseURL}/grow/properties/new`;
            }
            const options = {headers: { 'Content-Type': 'application/json' }};
            axios.post(path, this.property, options)
                 .then(() => {
                     this.postError = null;
                     this.$emit('posted');
                    })
                 .catch(err => {this.postError = `${err.response.data}`;})
        },

        postRefresh() {
        const path = `${baseURL}/devices/${this.device.id}/refresh`;
        this.refresh_is_loading = true;
        axios.post(path)
            .finally(() => {
            this.refresh_is_loading = false;
            });
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

        getGrowSystems() {
            const path = `${baseURL}/grow/systems`;
            this.systems_is_loading = true;
            console.debug(`GET: ${path}`);
            axios.get(path)
            .then(res => {
                console.debug(`data: ${res}`);
                this.growSystems = res.data;
            })
            .catch(err => {
                this.systems_error = err;
            })
            .finally(() => {
                this.systems_is_loading = false;
            });
        },
    },

    created() {
        if (this.prop_in) {
            this.property = {
                ...this.prop_in
            };
        }
    }
};
</script>

<style>

</style>
