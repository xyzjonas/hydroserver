<template>
  <div>
    <!-- just here to trigger the update -->
    <div class="is-hidden">{{ grow_property }}</div>
    <div v-if="title" class="title">
      {{ title }}
    </div>
    <div>
      <canvas id="planet-chart"></canvas>
    </div>

    <div class="tabs is-toggle is-fullwidth is-small mt-2">
      <ul>
        <li :class="{'is-active': tab == 'all', disabled: loading }" v-on:click="clickAll">
          <a v-if="loading"><div class="loader"></div></a>
          <a v-else><span>All</span></a>
        </li>
        <li :class="{'is-active': tab == 'month', disabled: loading }" v-on:click="clickMonth">
          <a v-if="loading"><div class="loader"></div></a>
          <a v-else><span>Month</span></a>
        </li>
        <li :class="{'is-active': tab == 'week', disabled: loading }" v-on:click="clickWeek">
          <a v-if="loading"><div class="loader"></div></a>
          <a v-else><span>Week</span></a>
        </li>
        <li :class="{'is-active': tab == 'day', disabled: loading }" v-on:click="clickDay">
          <a v-if="loading"><div class="loader"></div></a>
          <a v-else><span>Day</span></a>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import Chart from 'chart.js';
import axios from 'axios';
import { baseURL } from "@/app.config";
// import { planetChartData as chartData } from '../assets/test-data';

export default {

  props: ['device_id', 'grow_property', 'title', 'color'],

  data() {
    return {
      tab: 'day',
      daysOfWeek: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],

      chart: null,
      fullSize: true,
      loading: true,

      // use this in updated hook, to decide whether to reload the chart
      property_last: null,
      device_id_last: null,

      chartData: {
        type: 'line',
        data: {
          labels: [],
          datasets: [
            {
              data: [],
              backgroundColor: this.color ? `${this.color}8F` : '#8fbc8b90',
              borderColor: this.color ? this.color : '#8fbc8b',
              borderWidth: 3,
            },
          ],
        },
        options: {
          legend: {
            display: false,
          },
          responsive: true,
          lineTension: 1,
          scales: {
            yAxes: [
              {
                ticks: {
                  beginAtZero: true,
                  padding: 25,
                },
              },
            ],
          },
        },
      },

    };
  },

  methods: {

    clickDay() {
      this.tab = 'day';
      const sinceDate = new Date();
      sinceDate.setDate(sinceDate.getDate() - 1);
      sinceDate.setHours(sinceDate.getHours(), 0, 0, 0);
      const sinceTimestamp = sinceDate.getTime();

      this.fetchChart((isoTimestamp) => {
        const date = new Date(isoTimestamp);
        const adjustedDate = new Date(
          Date.UTC(
            date.getFullYear(),
            date.getMonth(),
            date.getDate(),
            date.getHours(),
            date.getMinutes(),
            date.getSeconds(),
          ),
        );
        return `${adjustedDate.getHours()}:${adjustedDate.getMinutes()}`;
      }, sinceTimestamp);
    },

    clickWeek() {
      this.tab = 'week';
      const sinceDate = new Date();
      sinceDate.setDate(sinceDate.getDate() - 7);
      sinceDate.setHours(0, 0, 0, 0);
      const sinceTimestamp = sinceDate.getTime();

      this.fetchChart((isoTimestamp) => {
        const date = new Date(isoTimestamp);
        const adjustedDate = new Date(
          Date.UTC(
            date.getFullYear(),
            date.getMonth(),
            date.getDate(),
            date.getHours(),
            date.getMinutes(),
            date.getSeconds(),
          ),
        );
        return `${adjustedDate.getDate()}.${adjustedDate.getMonth()}.${adjustedDate.getFullYear()}`;
      }, sinceTimestamp);
    },

    clickMonth() {
      this.tab = 'month';
      const sinceDate = new Date();
      sinceDate.setDate(sinceDate.getDate() - 30);
      sinceDate.setHours(0, 0, 0, 0);
      const sinceTimestamp = sinceDate.getTime();

      this.fetchChart((isoTimestamp) => {
        const date = new Date(isoTimestamp);
        const adjustedDate = new Date(
          Date.UTC(
            date.getFullYear(),
            date.getMonth(),
            date.getDate(),
            date.getHours(),
            date.getMinutes(),
            date.getSeconds(),
          ),
        );
        return `${adjustedDate.getDate()}.${adjustedDate.getMonth()}.${adjustedDate.getFullYear()}`;
      }, sinceTimestamp);
    },

    clickAll() {
      this.tab = 'all';
      this.fetchChart((isoTimestamp) => {
        const date = new Date(isoTimestamp);
        const adjustedDate = new Date(
          Date.UTC(
            date.getFullYear(),
            date.getMonth(),
            date.getDate(),
            date.getHours(),
            date.getMinutes(),
            date.getSeconds(),
          ),
        );
        return `${adjustedDate.getDate()}.${adjustedDate.getMonth()}.${adjustedDate.getFullYear()}`;
      });
    },

    createChart(labels, values) {
      // Spawn the chart with supplied x's and y's
      this.chartData.data.labels = labels;
      this.chartData.data.datasets[0].data = values;

      this.chartData.data.datasets[0].backgroundColor = this.color ? `${this.color}8F` : '#8fbc8b90';
      this.chartData.data.datasets[0].borderColor = this.color ? this.color : '#8fbc8b';

      const ctx = document.getElementById('planet-chart');

      // Destroy the old instance to prevent graph flickering
      if (this.chart) {
        this.chart.destroy();
      }
      this.chart = new Chart(ctx, this.chartData);
    },

    fetchChart(labelMapper, since = '', itemCount = 300) {
      const path = `${baseURL}/devices/${this.device_id}/sensors/${this.grow_property.sensor.id}/history?count=${itemCount}&since=${since}`;
      this.loading = true;
      axios.get(path)
        .then((res) => {
          this.error = null;
          const labels = res.data
            .map((x) => x.timestamp)
            .map(labelMapper);
          const values = res.data.map((x) => x.value);
          this.createChart(labels, values);
        })
        .catch((err) => {
          this.error = err;
          console.log(err.response);
          setTimeout(() => { this.error = null; }, 5000);
        })
        .finally(() => {
          this.loading = false;
        });
    },

  },

  mounted() {
    this.clickDay();
    this.property_last = this.grow_property;
    this.device_id_last = this.device_id;
  },

  updated() {
    if (this.property_last.id !== this.grow_property.id) {
      // property changed, reload graph
      this.property_last = this.grow_property;
      this.clickDay();
    } else if (this.device_id && this.device_id_last !== this.device_id) {
      // device changed, reload graph
      this.device_id_last = this.device_id;
      this.clickDay();
    }
  },

};
</script>
<style>
.loader {
  border: 0.1em solid #8fbc8b90; /* Light grey */
  border-top: 0.1em solid #1E5631; /* Blue */
  /* border-radius: 50%; */
  width: 1.5em;
  height: 1.5em;
  animation: spin 1s linear infinite;
}

.disabled {
    pointer-events:none; /* This makes it not clickable */
    opacity:0.6;         /* This grays it out to look disabled */
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
