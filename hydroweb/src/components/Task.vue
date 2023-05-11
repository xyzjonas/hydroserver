<template>
  <!-- CARD -->
  <div class="card mt-1 mb-1">

    <!-- HEADER -->
    <header class="card-header">
      <p v-on:click="toggleDetail" class="card-header-title">
        <img v-if="task.paused" class="icon is-small" src="status_paused.png"/>
        <span v-else-if="!device.scheduler_running" class="dot has-background-warning"/>
        <span v-else :class="{
              dot: true,
              'has-background-success': task.last_run_success,
              'has-background-danger': !task.last_run_success,
            }"/>

        <span class="mx-4">{{ task.name }}</span>

      </p>

      <!-- PLAY/PAUSE - only for unlocked tasks -->
      <a v-if="!task.locked" v-on:click="postResumeTask" class="card-header-icon">
        <i class="fa fa-play " aria-hidden="true"></i>
      </a>
      <a v-if="!task.locked" v-on:click="postPauseTask" class="card-header-icon">
        <i class="fa fa-pause" aria-hidden="true"></i>
      </a>
    </header>

    <!-- CONTENT -->
    <TaskDetail v-if="is_detail && !is_edit" :task="task"/>

    <TaskEdit v-if="is_edit" :device="device" :task="task" @cancel="is_edit=false"/>

    <!-- DETAIL FOOTER -->
    <footer class="card-footer"
      v-bind:class="{'is-hidden': !is_detail || is_edit}">

      <a v-if="!is_delete_modal" v-on:click="toggleEdit()" class="card-footer-item">
        Edit
      </a>
      <a v-if="!is_delete_modal && !task.locked" v-on:click="toggleDeleteModal()"
      class="card-footer-item has-text-danger">
        Delete
      </a>
      <a v-if="!is_delete_modal" v-on:click="toggleDetail()"
         class="card-footer-item has-text-black">
        Cancel
      </a>
      <!-- really delete? -->
      <a v-if="is_delete_modal" v-on:click="deleteTask()"
         class="card-footer-item has-text-danger">
        <strong>You sure? Yes!</strong>
      </a>
      <a v-if="is_delete_modal" v-on:click="toggleDeleteModal()"
         class="card-footer-item">
        Cancel
      </a>
    </footer>

  <!-- <div :id="`task-${task.id}-detail`"></div> -->

</div>
</template>

<script>
import axios from 'axios';
import TaskDetail from './TaskDetail.vue';
import TaskEdit from './TaskEdit.vue';
import { prettyDate } from './utils';
import { baseURL } from "@/app.config";

export default {
  props: ['task', 'device'],

  components: { TaskEdit, TaskDetail },

  data() {
    return {
      is_edit: false,
      is_delete_modal: false,
      is_detail: false,
      delete_error: null,
      edit_error: null,

      editTaskInterval_l: 20,
      editTaskInterval_r: 25,
      editTaskData: {
        id: this.task.id,
        name: this.task.name,
        type: this.task.type,
        cron: this.task.cron,
      },
    };
  },

  methods: {
    toggleEdit() {
      this.is_edit = !this.is_edit;
      // this.$refs['task-edit'].focus();
    },
    toggleDeleteModal() {
      this.is_delete_modal = !this.is_delete_modal;
    },
    toggleDetail() {
      this.is_detail = !this.is_detail;
      if (this.is_detail) {
        // document.getElementById(`task-${this.task.id}-detail`).scrollIntoView();
      }
    },
    formatTime(timeString) {
      return prettyDate(timeString);
    },
    postTask() {
      const path = `${baseURL}/devices/${this.device.id}/tasks`;
      const options = {
        headers: { 'Content-Type': 'application/json' },
      };
      if (this.editTaskData.type === 'interval') {
        this.editTaskData.meta.interval = `${this.editTaskInterval_l}-${this.editTaskInterval_r}`;
      } else {
        delete this.editTaskData.meta.interval;
      }
      axios.post(path, this.editTaskData, options)
        .then(() => {
          this.edit_error = null;
        })
        .catch((err) => {
          this.edit_error = err.response.data;
        });
      this.is_edit = false;
      this.is_detail = true;
    },
    postPauseTask() {
      const path = `${baseURL}/devices/${this.device.id}/tasks/${this.task.id}/pause`;
      axios.post(path);
    },
    postResumeTask() {
      const path = `${baseURL}/devices/${this.device.id}/tasks/${this.task.id}/resume`;
      axios.post(path);
    },
    deleteTask() {
      const path = `${baseURL}/devices/${this.device.id}/tasks/${this.task.id}`;
      axios.delete(path)
        .then(() => {
          this.toggleDeleteModal();
          this.delete_error = null;
        })
        .catch((e) => {
          this.delete_error = e.response.data;
        });
    },
  },

  created() {
    if (this.task.control) {
      this.editTaskData.control = this.task.control.name;
    }
    if (this.task.sensor) {
      this.editTaskData.sensor = this.task.sensor.name;
    }
    if (this.task.meta) {
      this.editTaskData.meta = this.task.meta;
    }
  },
};
</script>

<style>

</style>
