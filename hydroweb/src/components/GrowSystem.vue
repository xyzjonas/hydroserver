<template>
  <div>
  <div v-if="!device.grow_system">

    <button
      v-on:click="fetch_available_systems"
      :class="{
        'mt-5': true,
        button: true,
        'is-fullwidth': true,
        'is-loading': fetching_systems,
    }">NO GROW SYSTEM ASSIGNED</button>

    <ul v-if="available_systems_list_displayed" class="menu-list">
      <li>
        <ul>
          <li
            v-for="(system, index) in available_systems"
            :key="index + 'system_type'"
          ><a v-on:click="assignSystem(system.id)">
              [{{ system.id }}] {{ system.name }}
            </a>
          </li>
        </ul>
      </li>
    </ul>

  </div>
  <div v-else>
    <!-- IS GROW SYSTEM -->
    <h2 class="title is-4">
      {{ device.grow_system.name }}
      <button
        v-if="!unassign_system_check"
        v-on:click="unassign_system_check = !unassign_system_check"
        class="delete" style="position: relative; top: 4px; left: 5px"></button>
    </h2>
    <p v-if="unassign_system_check" class="subtitle is-6 has-text-danger">
      <small>Unassign system?</small
    ></p>
    <div v-if="unassign_system_check" class="level is-mobile">
      <div class="level-item">
        <button
          v-on:click="unassignSystem"
          class="button is-fullwidth is-small is-danger" style="">Yes</button>
      </div>
      <div class="level-item">
        <button
          v-on:click="unassign_system_check = !unassign_system_check"
          class="button is-fullwidth is-small">Cancel</button>
      </div>
    </div>

    <p v-else class="subtitle is-6"><small>assigned system</small></p>

    <div v-for="(property, index) in device.grow_system.grow_properties"
        :key="index + 'grow_prop'"
    >
      <GrowProperty :device="device" :property="property"/>
    </div>

    <hr>

    <!-- chart -->
    <div v-if="device.grow_system && graph_property">
      <div class="tabs is-toggle is-fullwidth is-small px-5 mb-3">
        <ul>
          <li
            v-for="(property, index) in device.grow_system.grow_properties"
            :key="'grow_prop_graph' + index"
            :class="{ 'is-active': graph_property.id === property.id}"
          >
            <a v-on:click="graph_property=property">{{ property.name }}</a>
          </li>
        </ul>
      </div>

      <div v-if="device.grow_system">
        <div v-if="graph_property && graph_property.sensor">
          <Chart
            :device_id="device.id"
            :grow_property="graph_property"
            :color="graph_property.color"
          />
        </div>

        <div v-else>
          <section class="hero is-medium is-light mx-5">
            <div class="hero-body">
              <p class="title">No data</p>
              <p class="subtitle is-6">No sensor assigned</p>
            </div>
          </section>
        </div>
      </div>

    </div>

  </div>

  </div>
</template>

<script>
import axios from 'axios';
import {baseURL} from "@/app.config";

import GrowProperty from './GrowProperty.vue';
import Chart from './Chart.vue';

export default {
  props: ['device'],

  components: { GrowProperty, Chart },

  data() {
    return {
      graph_property: null,
      // used in update hook, reset the selected property upon device change
      device_id_last: null,

      available_systems_list_displayed: false,
      available_systems: [],
      fetching_systems: false,

      unassign_system_check: false,
    };
  },

  methods: {

    assignSystem(systemId) {
      const path = `${baseURL}/grow/systems/assign`;
      const options = {
        headers: { 'Content-Type': 'application/json' },
      };
      const data = {
        system_id: systemId,
        device_id: this.device.id
      };
      axios.post(path, data, options)
        .then(() => {
        })
        .catch(() => {
        })
        .finally(() => {
          this.available_systems_list_displayed = false;
        });
    },
    unassignSystem() {
      const path = `${baseURL}/grow/systems/unassign/${this.device.id}`;
      axios.delete(path)
        .then(() => {
        })
        .catch(() => {
        })
        .finally(() => {
          this.available_systems_list_displayed = false;
          this.unassign_system_check = false;
        });
    },

    fetch_available_systems() {
      if (this.available_systems_list_displayed) {
        this.available_systems_list_displayed = false;
        return;
      }
      const path = `${baseURL}/grow/systems`;
      this.fetching_systems = true;
      axios.get(path)
        .then((res) => {
          this.available_systems = res.data;
        })
        .catch(() => {
          // todo
        })
        .finally(() => {
          this.fetching_systems = false;
          this.available_systems_list_displayed = true;
        });
    },

  },

  updated() {
    if (!this.graph_property && this.device.grow_system) {
      // new page load, select the first property once the device object is available
      [this.graph_property] = this.device.grow_system.grow_properties;
      this.device_id_last = this.device.id;
    } else if (this.device.grow_system && this.device_id_last !== this.device.id) {
      // different device selected, reselect its first property to render the graph
      [this.graph_property] = this.device.grow_system.grow_properties;
      this.device_id_last = this.device.id;
    }
  },

  created() {
  },

};
</script>

<style>

</style>
