<template>
<div>
  <!-- add task -->
  <div class="card-content">

    <TaskForm :device="device" :task="editTaskData"></TaskForm>

    <article v-if="addTaskError" class="message is-danger">
      <div class="message-body">
        <strong>Edit task failed:</strong> {{ addTaskError }}
      </div>
    </article>
  </div>
  <footer class="card-footer">
    <a v-on:click="postTask()" class="is-success card-footer-item">Save</a>
    <a v-on:click="cancel()" class="card-footer-item">Cancel</a>
  </footer>
</div>
</template>

<script>
import axios from 'axios';
import { baseURL } from "@/app.config";
import TaskForm from './TaskForm.vue';

export default {
  props: ['device', 'task'],
  components: { TaskForm },

  data() {
    return {
      isEdit: false,

      available_tasks: [],

      metaPairs: [[]],
      editTaskData: {
        meta: {},
      },
      addTaskError: null,
    };
  },

  methods: {

    cancel() {
      this.$emit('cancel');
    },

    postTask() {
      const path = `${baseURL}/devices/${this.device.id}/tasks`;
      const options = {
        headers: { 'Content-Type': 'application/json' },
      };

      axios.post(path, this.editTaskData, options)
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
    // copy/map the task object (which changes with each 'tick') to a local copy
    this.editTaskData = JSON.parse(JSON.stringify(this.task));
    if (this.editTaskData.control) {
      this.editTaskData.control = this.editTaskData.control.name;
    }
    if (this.editTaskData.sensor) {
      this.editTaskData.sensor = this.editTaskData.sensor.name;
    }
    this.metaPairs = [];
    Object.entries(this.editTaskData.meta).forEach(([key, value]) => {
      this.metaPairs.push([key, value]);
    });

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
