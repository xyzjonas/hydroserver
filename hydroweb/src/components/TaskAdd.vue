<template>
  <!-- add task -->
  <!-- <button v-on:click="toggleEdit()" class="button is-success is-fullwidth mt-2"
  v-bind:disabled="isEdit">
  <i class="fa fa-plus"></i></button> -->

  <!-- add task -->
  <div class="card mt-1 mt-4">
    <header class="card-header">
      <p class="card-header-title is-1">Add a new task</p>
    </header>
  <div class="card-content">
    <TaskForm :device="device" :task="addTaskData"></TaskForm>

    <article v-if="addTaskError" class="message is-danger">
      <div class="message-body">
        <strong>Add task failed:</strong> {{ addTaskError }}
      </div>
    </article>
  </div>
  <footer class="card-footer">
    <a v-on:click="postTask()" class="is-success card-footer-item">Add</a>
    <a v-on:click="cancel()" class="card-footer-item">Cancel</a>
  </footer>
</div>
</template>

<script>
import axios from 'axios';
import {baseURL} from "@/app.config";
import { prettyDate } from './utils';
import TaskForm from './TaskForm.vue';

export default {
  props: ['device'],
  components: { TaskForm },

  data() {
    return {
      isEdit: false,

      available_tasks: [],

      metaPairs: [[]],
      addTaskData: {
        meta: {},
      },
      addTaskError: null,
    };
  },

  methods: {

    printT() {
      return prettyDate('asdads');
    },

    cancel() {
      this.$emit('cancel');
    },

    postTask() {
      const path = `${baseURL}/devices/${this.device.id}/tasks`;
      const options = {
        headers: { 'Content-Type': 'application/json' },
      };

      axios.post(path, this.addTaskData, options)
        .then(() => {
          this.addTaskError = null;
          this.cancel();
        })
        .catch((err) => {
          this.addTaskError = err.response.data;
        });
      this.editing_mode = false;
    },
  },

  created() {
    const rootPath = `${baseURL}/`;
    axios.get(rootPath)
      .then((res) => {
        this.available_tasks = res.data.tasks;
      })
      .catch((err) => {
        console.error(err);
      });
  },
};

</script>

<style>

</style>
