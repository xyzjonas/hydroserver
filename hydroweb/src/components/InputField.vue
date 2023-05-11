<template>
<div>
  <div v-show="editing_mode" class="control level-item">
    <input v-model="form_name" v-bind:placeholder="device.name"
          class="input is-primary" type="text" ref="form_name">
    <button class="button ml-2">
      <span v-on:click="updateName" class="icon is-medium"><img src="save_ico.png"/></span>
    </button>
    <button v-on:click="toggleEdit" class="button ml-1">
      <span class="icon is-medium"><img src="cancel_ico.png"/></span>
    </button>
  </div>
</div>
</template>

<script>
export default {
  props: ['data'],
};
</script>

<style>

</style>
