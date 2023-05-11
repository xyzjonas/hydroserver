<template>
<div>
    <!-- DEVICE DETAILS -->
    <div class="level">
        <div class="level-left title is-6">uuid</div>
        <div class="level-right subtitle is-6">{{ device.uuid }}</div>
    </div>
    <div class="level">
        <div class="level-left title is-6">Name</div>
        <div class="level-right subtitle is-6">{{ device.name }}</div>
    </div>
    <div class="level">
        <div class="level-left title is-6">Type</div>
        <div class="level-right subtitle is-6">{{ device.type }}</div>
    </div>
    <div class="level">
        <div class="level-left title is-6">URL</div>
        <div class="level-right subtitle is-6">{{ device.url }}</div>
    </div>

    <hr>

    <!-- REFRESH -->
    <div class="level">
    <div class="level-left">
        <p>Reconnect (try to re-establish connection)</p>
    </div>
    <div class="level-right subtitle is-6">
        <button v-on:click="postRefresh"
        :class="{
            button:true,
            'is-loading': refresh_is_loading,
            'is-outlined':true,
            'is-fullwidth':true
        }" style="min-width: 10em;"
        >
        <span v-if="!refresh_is_loading">Reconnect</span>
        </button>
    </div>
    </div>

    <!-- CLEAR HISTORY -->
    <div class="level">
    <div class="level-left">
        <p>Clear sensor history</p>
    </div>
    <div class="level-right subtitle is-6">
        <button v-on:click="postClearHistory"
        :class="{
            button:true,
            'is-loading': clear_is_loading,
            'is-outlined':true,
            'is-fullwidth':true
        }" style="min-width: 10em;"
        >
        <span v-if="!clear_is_loading">Clear all</span>
        <span v-else>{{ clearLoadingMessage }}</span>
        </button>
    </div>
    </div>

    <hr>
    <p class="menu-label">SYSTEM TASKS</p>
      <div v-for="(t, index) in device.tasks" :key="'task-settings-'+index">
        <div v-if="t.locked">
          <Task :task="t" :device_id="device.id" :device="device"></Task>
        </div>
      </div>

    <hr>

    <div v-if="properties_error">
    ERROR:  {{ properties_error }}
    </div>
    
    <div class="menu">
        <div class="level is-mobile mb-0">
            <div class="level-left m-0 p-0">
                <p class="menu-label m-0 mr-3">GROW PROPERTIES</p>
                <button v-on:click="newProperty = !newProperty" class="button is-success is-small is-outlined">
                    <i class="fa fa-plus"></i>
                </button>
            </div>
        </div>
        <div v-if="newProperty">
            <p class="ml-3 mt-2 has-text-success">Add new grow property</p>
            <GrowPropertyForm
                @cancel="newProperty = false"
                @posted="getGrowProperties(); newProperty = false"
            ></GrowPropertyForm>
        </div>
        <ul class="menu-list mt-2">
            <li v-for="(prop, index) in growProperties" :key="index + '-grow-prop'">
                <a v-on:click="selectProperty(index)"
                  :class="{
                    'is-active': selectedProperty == index
                  }"
                ><strong>{{ prop.name }}</strong><span v-if="prop.description"> : {{ prop.description }}</span></a>
                <ul v-if="selectedProperty == index && !property_is_editing">
                    <li v-if="!deletePropertyAreYouSure"><a v-on:click="property_is_editing = true">Edit</a></li>
                    <li v-if="!deletePropertyAreYouSure">
                        <a 
                        v-on:click="deletePropertyAreYouSure = true"
                        class="has-text-danger">
                            Delete
                        </a>
                    </li>
                    <li  v-if="deletePropertyAreYouSure">
                        <div class="level">
                            <p class="has-text-danger">Are you sure?</p>
                            <div class="level-right mt-2">
                                <button v-on:click="deleteProperty(prop)" class="button is-danger is-outlined mr-2 is-small">Delete</button>
                                <button v-on:click="deletePropertyAreYouSure = false" class="button is-outlined is-small">Cancel</button>
                            </div>
                        </div>
                    </li>
                </ul>
                <div v-if="selectedProperty == index && property_is_editing">
                    <GrowPropertyForm :prop_in="growProperties[index]"
                        @cancel="property_is_editing = false; selectedProperty = 999"
                        @posted="getGrowProperties(); property_is_editing = false; selectedProperty = null"
                    ></GrowPropertyForm>
                </div>
            </li>
        </ul>

        <hr>

        <div class="level is-mobile mb-0">
            <div class="level-left m-0 p-0">
                <p class="menu-label m-0 mr-3">GROW SYSTEMS</p>
                <button v-on:click="newSystem = !newSystem" class="button is-success is-small is-outlined">
                    <i class="fa fa-plus"></i>
                </button>
            </div>
        </div>
        
        <div v-if="newSystem">
            <p class="ml-3 mt-2 has-text-success">Add new grow system</p>
            <GrowSystemForm
                @cancel="newSystem = false"
                @posted="getGrowSystems(); newSystem = false"
            ></GrowSystemForm>
        </div>

        <ul class="menu-list mt-2">
            <li v-for="(system, index) in growSystems" :key="index + '-grow-system'">
                <a v-on:click="selectSystem(index)"
                  :class="{
                    'is-active': selectedSystem == index
                  }"
                ><b>{{ system.name }}</b></a>
                <ul v-if="selectedSystem == index && !systems_is_editing">
                    <li v-if="!deleteSystemAreYouSure" v-on:click="systems_is_editing = true"><a>Edit</a></li>
                    <li v-if="!deleteSystemAreYouSure"><a v-on:click="deleteSystemAreYouSure = true" class="has-text-danger">Delete</a></li>
                    <li  v-if="deleteSystemAreYouSure">
                        <div class="level">
                            <p class="has-text-danger">Are you sure?</p>
                            <div class="level-right mt-2">
                                <button v-on:click="deleteSystem(system)" class="button is-danger is-outlined mr-2 is-small">Delete</button>
                                <button v-on:click="deleteSystemAreYouSure = false" class="button is-small">Cancel</button>
                            </div>
                        </div>
                    </li>
                </ul>
                <div v-if="selectedSystem == index && systems_is_editing">
                    <GrowSystemForm :system_in="system"
                        @cancel="systems_is_editing = false; selectSystem()"
                        @posted="getGrowSystems(); systems_is_editing = false; selectedSystem = null"
                    ></GrowSystemForm>
                </div>
            </li>
        </ul>
       
    </div>

    <hr>

        <!-- DELETE -->
    <div class="level mb-5">
    <div class="level-left">
        <p>Remove this device (and all associated data)</p>
    </div>
    <div class="level-right subtitle is-6">
        <button v-on:click="postDelete()"
        :class="{
            button:true,
            'is-danger':true,
            'is-outlined':true,
            'is-fullwidth':true
        }" style="min-width: 10em;"
        >
        Remove
        </button>
    </div>
    </div>

</div>
</template>

<script>
import axios from 'axios';
import {baseURL} from "@/app.config";
import GrowPropertyForm from './GrowPropertyForm.vue';
import GrowSystemForm from './GrowSystemForm.vue';
import Task from './Task.vue';

export default {
    props: ["device"],
    components: {
        GrowPropertyForm, GrowSystemForm, Task
    },
    
    data() {
        return {
            refresh_is_loading: false,
            clear_is_loading: false,
            clearLoadingMessage: null,

            growProperties: [],
            selectedProperty: null,
            properties_error: "",
            properties_is_loading: false,
            property_is_editing: false,

            newProperty: false,
            deletePropertyAreYouSure: false,

            growSystems: [],
            selectedSystem: null,
            systems_error: "",
            systems_is_loading: false,
            systems_is_editing: false,

            newSystem: false,
            deleteSystemAreYouSure: false,
        };
    },
    methods: {
        
        selectProperty(index) {
            this.property_is_editing = false;
            if (this.selectedProperty == index) {
                this.selectedProperty = null;
            } else {
                this.selectedProperty = index;
            }
        },
        
        deleteProperty(property) {
            const path = `${baseURL}/grow/properties/${property.id}`;
            axios.delete(path)
                 .finally(() => {
                     this.selectedSystem = null;
                     this.deletePropertyAreYouSure = false;
                     this.getGrowProperties();
                 })
        },

        deleteSystem(system) {
            const path = `${baseURL}/grow/systems/${system.id}`;
            axios.delete(path)
                 .finally(() => {
                     this.selectedSystem = null;
                     this.deleteSystemAreYouSure = false;
                     this.getGrowSystems();
                 })
        },

        selectSystem(index) {
            if (this.selectedSystem == index) {
                this.selectedSystem = null
            } else {
                this.selectedSystem = index
            }
        },

        postDelete() {
            const path = `${baseURL}/devices/${this.device.id}`;
            axios.delete(path);
        },

        postRefresh() {
            const path = `${baseURL}/devices/${this.device.id}/refresh`;
            this.refresh_is_loading = true;
            axios.post(path)
                .finally(() => {
                this.refresh_is_loading = false;
            });
        },
        
        clearHistoryRecursively(index, sensorIds) {
            const path = `${baseURL}/devices/${this.device.id}/sensors/`;
            this.clearLoadingMessage = `${index}/${sensorIds.length}`;
            if (!sensorIds[index]) {
                setTimeout(() => {this.clear_is_loading = false;}, 1000);
                return;
            }
            console.debug(`Deleting ${index}/${sensorIds.length}: sensor id: ${sensorIds[index]}`);
            axios.delete(path + sensorIds[index] + '/history')
                 .finally(() => {
                     if (index >= sensorIds.length - 1) {
                         this.clear_is_loading = false;
                     } else {
                         this.clearHistoryRecursively(index+=1, sensorIds);
                     }
                 })
        },

        postClearHistory() {
            console.debug(this.device.sensors);
            console.debug(this.device.sensors[0]);
            var sensorIds = this.device.sensors.map(s => s.id);
            console.debug(sensorIds);
            var sensor_index = 0;
            
            this.clear_is_loading = true;
            this.clearHistoryRecursively(sensor_index, sensorIds);
        },

        getGrowProperties() {
            const path = `${baseURL}/grow/properties`;
            this.properties_is_loading = true;
            axios.get(path)
                .then(res => {
                this.growProperties = res.data;
            })
                .catch(err => {
                this.properties_error = err;
            })
                .finally(() => {
                this.properties_is_loading = false;
            });
        },
        
        getGrowSystems() {
            const path = `${baseURL}/grow/systems`;
            this.systems_is_loading = true;
            console.debug(`GET: ${path}`);
            axios.get(path)
                .then(res => {
                console.debug(`data: ${res}`);
                this.growSystems = res.data;
            })
                .catch(err => {
                this.systems_error = err;
            })
                .finally(() => {
                this.systems_is_loading = false;
            });
        },
    },
    created() {
        this.getGrowProperties();
        this.getGrowSystems();
    },

};
</script>

<style>

</style>
