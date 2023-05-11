<template>
  <div>
    <!-- <div v-if="!device.grow_plan">
      <button class="my-5 button is-fullwidth">NO GROW PLAN ASSIGNED</button>
    </div> -->

    <div>
      <article class="media">
          <figure class="media-left">
            <p class="image is-96x96">
              <img class="is-rounded" src="https://trevisanuttos.com/wp-content/uploads/2020/04/Basil-Sweet-Genovese.jpeg">
            </p>
          </figure>
          <div class="media-content">
            <div class="content">
              <p>
                <strong>Herbs</strong>
                <br>
                <small>Planted: 15 Aug 2021</small>
              </p>
              <hr>
              <progress class="progress is-large mb-0 is-primary" value="88" max="100"/>
              <div class="level p-0">
                <div class="level-item p-0 m-0">
                  <p class="content"><small>40 days out of 45</small></p>
                </div>
              </div>
            </div>
          </div>
      </article>
    </div>

  </div>
</template>

<script>
import axios from 'axios';
import {baseURL} from "@/app.config";

export default {
  props: ['device'],

  data() {
    return {
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
        })
        .catch(() => {
        });
    },
    sensorDelete() {
      // const path = `${baseURL}/devices/${this.device.id}/sensors/${id}`;
      // axios.delete(path);
    },

  },

};
</script>

<style>

</style>
