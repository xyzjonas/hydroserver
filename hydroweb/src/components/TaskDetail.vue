<template>

<!-- CARD CONTENT -->
<div class="card-content">
  <div class="content">
    <div class="level mb-2 is-mobile">
      <div class="level-left">Type</div>
      <div class="level-right">
          <strong>{{ task.type }}</strong>
      </div>
    </div>
    <div class="level mb-2 is-mobile">
      <div class="level-left">Schedule</div>
      <div class="level-right">
        <strong>{{ task.cron }}</strong>
      </div>
    </div>
    <div v-if="task.control" class="level mb-2 is-mobile">
      <div class="level-left">Control</div>
      <div class="level-right">
          <strong>{{ task.control ? task.control.description : "no control"}}</strong>
      </div>
    </div>
    <div v-if="task.sensor" class="level mb-2 is-mobile">
      <div class="level-left">Sensor</div>
      <div class="level-right">
          <strong>{{ task.sensor ? task.sensor.description : "no sensor"}}</strong>
      </div>
    </div>
    <div class="level mb-2 is-mobile">
      <div class="level-left">Last run</div>
      <div class="level-right">
          <strong>{{ task.last_run ? formatTime(task.last_run) : 'not yet'}}</strong>
      </div>
    </div>

    <!-- error -->
    <div v-if="task.last_run_error" class="level mb-2">
      <div class="level-left">Error</div>
      <div class="level-right">
          <strong class="has-text-danger">{{ task.last_run_error }}</strong>
      </div>
    </div>

    <!-- meta -->
    <div v-if="Object.keys(task.meta).length > 0">
      <hr>
      <h6>Meta</h6>
      <div class="columns is-mobile">
        <div class="column">
          <p v-for="(v, k) in task.meta" :key="'metak'+k" >{{k}}</p>
        </div>
        <div class="column is-half has-text-right">
          <p v-for="(v, k) in task.meta" :key="'metav'+k">{{v}}</p>
        </div>
      </div>
    </div>

  </div>
</div>
</template>

<script>
import { prettyDate } from './utils';

export default {
  props: ['task'],

  methods: {
    formatTime(str) {
      return prettyDate(str);
    },
  },
};
</script>
