<template>
<div class="mt-5">

<div class="container px-4">
    <!-- TITLE  + edit name -->
    <div class="level">
      <div v-show="editing_mode" class="control level-item">
        <input v-model="form_name" v-bind:placeholder="device.name"
              class="input is-primary" type="text" ref="form_name">
        <button v-on:click="updateName" class="button ml-2">
            <span class="icon is-small">
            <i class="fas fa-check"></i>
          </span>
        </button>
        <button v-on:click="toggleEdit" class="button ml-1">
          <span class="icon is-small">
            <i class="fas fa-times"></i>
          </span>
        </button>
      </div>
      <h1 v-if="!editing_mode" class="title">
        {{ device.name }}
        <a v-on:click="toggleEdit" class="icon"><img src="edit_ico.png"/></a>
      </h1>
    </div>
    <!-- last update -->
    <div class="level is-mobile ">
      <div class="level-left">
        <div class="level-item">
          <span v-if="!device.scheduler_running" class="dot has-background-warning"/>
          <span v-else :class="{
              dot: true,
              'has-background-success': device.is_online,
              'has-background-danger': !device.is_online,
            }"/>
        </div>
        <div class="level-item">
          <p v-if="device.is_online" class="subtitle is-5">
            last update: {{ formatTime(device.time_modified) }}
          </p>
          <p v-else class="subtitle is-5">
            last seen online: {{ formatTime(device.last_seen_online) }}
          </p>
        </div>
      </div>
    </div>

    <!-- TABS -->
    <div class="tabs is-centered mt-5">
    <ul>
      <li v-bind:class="{ 'is-active': tab === 'home' }">
        <a v-on:click="tab = 'home'; triggerRefresh()">
          <span class="icon">
            <i class="fas fa-seedling" aria-hidden="true"></i>
          </span>
        </a>
      </li>
      <li v-bind:class="{ 'is-active': tab === 'stats' }">
        <a v-on:click="tab = 'stats'">
          <span class="icon">
            <i class="fas fa-server" aria-hidden="true"></i>
          </span>
        </a>
      </li>
      <li v-bind:class="{ 'is-active': tab === 'settings' }">
        <a v-on:click="tab = 'settings'">
          <span class="icon">
            <i class="fas fa-cog" aria-hidden="true"></i>
          </span>
        </a>
      </li>
    </ul>
    </div>

    <div v-if="tab === 'home'" class="container">

      <!-- plant -->
      <GrowPlan :device="device"/>

      <hr>

      <GrowSystem :device="device"/>

      <hr>

    </div>
    <!-- STATS -->
    <div v-if="tab === 'stats'" class="container">
      <!-- scheduler -->
      <article v-if="device.scheduler_running" class="message is-success my-1">
        <div class="message-body">
          Scheduler is <strong>running</strong>
        </div>
      </article>
      <article v-else class="message is-warning my-1">
        <div class="message-body">
          Scheduler is <strong>stopped</strong>
          <a v-on:click="postScheduler()" class="ml-5">
            <i class="fas fa-play"/>
          </a>
          <br>
          <!-- scheduler error - nested inside the warning message body -->
          <span v-if="device.scheduler_error">{{ device.scheduler_error }}</span>
        </div>
      </article>
      
      <!-- sensors -->
      <h4 v-if="device.sensors.length > 0" class="subtitle mt-5">Sensors</h4>
      <div v-for="(sensor, index) in device.sensors" :key="'dev_sensor' + index">
        <Sensor :sensor="sensor" :device="device"></Sensor>
      </div>

      <!-- controls -->
      <h4 v-if="device.controls.length > 0" class="subtitle mt-5">Controls</h4>
      <div v-for="(control, index) in device.controls" :key="'dev_control' + index">
        <Control :control="control" :device="device"></Control>
      </div>

      <!-- tasks -->
      <h4  class="subtitle mt-5">TASKS</h4>
      <div v-for="(t, index) in device.tasks" :key="'task'+index">
        <div v-if="!t.locked">
          <Task :task="t" :device_id="device.id" :device="device"></Task>
        </div>
      </div>
      <article v-if="device.tasks.length == 0" class="message is-warning">
        <div class="message-body">
          <small><strong>No tasks yet</strong></small>
        </div>
      </article>

      <!-- add task -->
      <button v-on:click="addTask=true" class="button is-success is-fullwidth mt-2 is-outlined"
        v-bind:disabled="addTask">
        <i class="fa fa-plus"></i>
      </button>
      <TaskAdd v-if="addTask" :device="device" @cancel="addTask=false"></TaskAdd>
    </div>

    <!-- SETTINGS -->
    <div v-if="tab === 'settings'" class="container">
      <Settings :device="device"></Settings>

    </div>
  </div>
</div>
</template>

<script>
import axios from 'axios';
import {baseURL} from "@/app.config";
import Settings from './Settings.vue';
import Task from './Task.vue';
import Control from './Control.vue';
import Sensor from './Sensor.vue';
import TaskAdd from './TaskAdd.vue';
import { prettyDate } from './utils';

import GrowSystem from './GrowSystem.vue';
import GrowPlan from './GrowPlan.vue';

export default {
  props: ['device'],

  components: {
    Task, Control, Sensor, TaskAdd, GrowSystem, GrowPlan, Settings
  },

  data() {
    return {
      // home / stats / settings
      tab: 'home',

      addTask: false,

      editing_mode: false,

      refresh_is_loading: false,

      // edit dev name
      form_name: this.device.name,

      // edit
      isCategorize: false,
      categorize: {},

      // home
      graph_sensor: this.device.sensors[0],
    };
  },

  methods: {
    // server communication
    updateName() {
      const path = `${baseURL}/devices/${this.device.id}`;
      const options = {
        headers: { 'Content-Type': 'application/json' },
      };
      const data = { name: this.form_name };
      axios.post(path, data, options)
        .then(() => {
          this.device.name = this.form_name;
        });
      this.editing_mode = false;
    },
    
    postScheduler() {
      const path = `${baseURL}/devices/${this.device.id}/scheduler`;
      axios.post(path);
    },
    
    toggleEdit() {
      this.editing_mode = !this.editing_mode;
    },

    // misc tools
    formatTime(timeString) {
      return prettyDate(timeString);
    },

    triggerRefresh() {
      this.$emit('triggerRefresh');
    },

  },
};
</script>
