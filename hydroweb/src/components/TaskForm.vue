<template>
<div>
  <!-- FORM ONLY -->
  <div class="field">
    <label class="label">Description</label>
    <div class="control">
      <input v-model="task.name"
      class="input" type="text" placeholder="describe the task">
    </div>
  </div>

  <!-- SCHEDULE -->
  <div class="field mt-5">
      <label class="label">Schedule</label>
      <div class="tabs is-fullwidth is-small">
        <ul>
          <li :class="{'is-active': schedule == 'daily'}">
            <a v-on:click="schedule = 'daily'">
              <!-- <span class="icon is-small"><i class="fas fa-image" aria-hidden="true"></i></span> -->
              <span>Daily</span>
            </a>
          </li>
          <li :class="{'is-active': schedule == 'interval'}">
            <a v-on:click="schedule = 'interval'">
              <!-- <span class="icon is-small"><i class="fas fa-music" aria-hidden="true"></i></span> -->
              <span>Interval</span>
            </a>
          </li>
          <li :class="{'is-active': schedule == 'cron'}">
            <a v-on:click="schedule = 'cron'">
              <!-- <span class="icon is-small"><i class="fas fa-music" aria-hidden="true"></i></span> -->
              <span>Cron (UTC)</span>
            </a>
          </li>
        </ul>
      </div>

      <!-- CRON -->
      <div id="schedule-cron" v-if="schedule == 'cron'">
        <div class="control">
          <input v-model="task.cron"
          class="input" type="text" placeholder="schedule in cron format">
        </div>
      </div>
      <!-- INTERVAL -->
      <div id="schedule-interval" v-if="schedule == 'interval'">
        <div class="level is-mobile">
          <div class="level-item">
            <span class="mr-3"><strong>Every</strong></span>
            <input v-model="intervalValue" class="input mr-2" type="number" style="width: 5em;">
            <div class="select">
              <select v-model="intervalType">
                <option>seconds</option>
                <option>minutes</option>
                <option>hours</option>
              </select>
            </div>
          </div>
        </div>
      </div>
      <!-- DAILY -->
      <div id="schedule-daily" v-if="schedule == 'daily'">
        <div class="level is-mobile is-size-7">
          <div class="level-item mr-1"><span class="mr-1">M</span><input v-on:change="toCron" v-model="weekdays[0]" type="checkbox"></div>
          <div class="level-item mr-1"><span class="mr-1">T</span><input v-on:change="toCron" v-model="weekdays[1]" type="checkbox"></div>
          <div class="level-item mr-1"><span class="mr-1">W</span><input v-on:change="toCron" v-model="weekdays[2]" type="checkbox"></div>
          <div class="level-item mr-1"><span class="mr-1">T</span><input v-on:change="toCron" v-model="weekdays[3]" type="checkbox"></div>
          <div class="level-item mr-1"><span class="mr-1">F</span><input v-on:change="toCron" v-model="weekdays[4]" type="checkbox"></div>
          <div class="level-item mr-1"><span class="mr-1">S</span><input v-on:change="toCron" v-model="weekdays[5]" type="checkbox"></div>
          <div class="level-item mr-1"><span class="mr-1">S</span><input v-on:change="toCron" v-model="weekdays[6]" type="checkbox"></div>
        </div>        

        <input 
          v-model="time"
          v-on:change="toCron"
          :class="{
            input:true,
            'is-success': time,
            'is-danger': !time
          }" type="time">
      </div>
  </div>

  <hr class="hr">

  <div class="field">
    <label class="label">Type</label>
    <div class="control">
      <div class="select is-fullwidth">
        <select v-model="task.type">
          <option v-for="(taskType, i) in available_tasks" :key="i + 'asd'">
            {{ taskType }}
          </option>
        </select>
      </div>
    </div>
  </div>

  <div class="field">
    <label class="label">Control</label>
    <div class="control">
      <div class="select is-fullwidth">
        <select v-model="task.control">
          <option v-for="(c, index) in device.controls" :key="'ccon'+index"
          :value="c.name">{{ c.description }}</option>
        </select>
      </div>
    </div>
  </div>

  <div class="field">
    <label class="label">Sensor</label>
    <div class="control">
      <div class="select is-fullwidth">
        <select v-model="task.sensor">
          <option v-for="(s, index) in device.sensors" :key="'ssens'+index"
          :value="s.name">{{ s.description }}</option>
        </select>
      </div>
    </div>
  </div>

  <!-- META -->
  <label class="label">Metadata</label>
  <div v-for="(meta, i) in Object.entries(task.meta)" :key="i + 'meta'" class="field">
    <div class="control has-icons-left">
      <input class="input" :placeholder="i + 1 + '. key'"
             v-model="tmpMetaKeys[i]" v-on:input="modifyMetaKey($event, meta[0], i)">
      <span class="icon is-left">
        <i class="fas fa-key"></i>
      </span>
    </div>
    <div class="control has-icons-left mt-1">
      <input class="input" placeholder="value" v-model="task.meta[meta[0]]">
      <span class="icon is-left">
        <i class="fas fa-font"></i>
      </span>
    </div>
    <hr>
  </div>

  <button class="button is-fullwidth"
  v-on:click="task.meta.newKey = ''; tmpMetaKeys.push['xx']">
    <i class="fa fa-plus"></i>
  </button>


  <article v-if="addTaskError" class="message is-danger mt-5">
    <div class="message-body">
      <strong>Add task failed:</strong> {{ addTaskError }}
    </div>
  </article>

</div>
</template>

<script>
import axios from 'axios';
import {baseURL} from "@/app.config";

export default {
  props: ['device', 'task'],

  data() {
    return {
      // Daily input
      weekdays: [true, true, true, true, true, true, true],
      time: null,
      schedule: "cron",

      // Interval input
      intervalType: 'seconds',
      intervalValue: 10,

      tmpMetaKeys: [],
      available_tasks: [],
      addTaskError: null,
    };
  },

  methods: {

    modifyMetaKey(event, oldKey, index) {
      // on key input change, update the actual task's meta
      const newKey = this.tmpMetaKeys[index];
      this.task.meta[newKey] = this.task.meta[oldKey];
      delete this.task.meta[oldKey];
    },

    pad(num, size) {
      num = num.toString();
      while (num.length < size) num = "0" + num;
      return num;
    },

    fromCron(cron) {
      const cronFields = cron.split(' ')
      // #1 cron can be represented as a time in day/days
      if(
        parseInt(cronFields[0])
        && parseInt(cronFields[1])
        && cronFields[2] == '*'
        && cronFields[3] == '*'
      ) {
        // todo: timezone offset will not work with daylight savings
        // => probably needs to be stored by the hydroserver.
        const minutes = parseInt(cronFields[0]);
        const utcHours = parseInt(cronFields[1]);
        const offset = (new Date().getTimezoneOffset() / 60);

        const hours = (utcHours - offset) % 24
        this.time = `${this.pad(hours, 2)}:${minutes}`;
        this.schedule = 'daily';

        const weekday = cronFields[4]
        // Week days as range
        if (weekday.split('-').length == 2) {
          const left = parseInt(weekday.split('-')[0]);
          const right = parseInt(weekday.split('-')[1]);
          this.weekdays = [false, false, false, false, false, false, false]
          for(var i=left-1; i<=right-1; i++) {
            this.weekdays[i] = true;
          }

        // Week days as list
        } else if (weekday.split(',').length > 1) {
          this.weekdays = [false, false, false, false, false, false, false];
          weekday.split(',').forEach(day => {
            this.weekdays[parseInt(day)-1] = true;
          })
        
        // Single week day
        }else if (parseInt(weekday)) {
          this.weekdays = [false, false, false, false, false, false, false]
          this.weekdays[parseInt(weekday) - 1] = true;

        // Every day
        } else if (weekday == '*') {
          this.weekdays = [true, true, true, true, true, true, true];
        }
      }
      // todo: #2 can be represented as interval
    },

    toCron() {
      if (this.schedule == 'daily') {
        if (!this.time) {
          this.addTaskError = 'Time needs to be filled in.';
          return false;
        }
        const hour = this.time.split(':')[0];
        const minute = this.time.split(':')[1];
        const weekdaysCron = [];
        for (var i=1; i < this.weekdays.length + 1; i++) {
          if (this.weekdays[i-1]) {
            weekdaysCron.push(i);
          }
        }

        const offset = (new Date().getTimezoneOffset() / 60);
        var hourWithOffset = (parseInt(hour) + offset) % 24
        if (hourWithOffset < 0) {
          hourWithOffset = 24 + hourWithOffset;
        }
        this.task.cron = `${minute} ${hourWithOffset} * * ${weekdaysCron.join(',')}`;
      }

      this.addTaskError = null;
      // default to the actual cron value
      return this.task.cron;
    }
  },

  created() {
    this.tmpMetaKeys = Object.keys(this.task.meta);
    
    if (this.task.cron){
      this.fromCron(this.task.cron);
    }

    // fetch available task types
    const rootPath = `${baseURL}/`;
    axios.get(rootPath)
      .then((res) => {
        this.available_tasks = res.data.tasks;
      })
      .catch((err) => {
        console.error(err);
        this.addTaskError = 'Failed to fetch available task types';
      });
  },
};

</script>

<style>

</style>

