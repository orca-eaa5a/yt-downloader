<template>
    <div class="full-screen">
        <div class="red-panel"></div>
        <div class="main-view">
            <div class="grid p-fluid w-100">
                <div class="col-12 md:col-3"></div>
                <div class="col-12 md:col-6">
                    <VideoPlayer  ref="player" class="video-layout mb-3"></VideoPlayer>
                    <div class="flex justify-content-between mb-3">
                        <p class="video-info video-length">test</p>
                        <div class="flex" style="max-width: 20rem; min-width: 17.2rem;">
                            <Button class="btn-red" icon="pi pi-download" label="재설정 요청"></Button>
                            <Button class="ml-2" icon="pi pi-download" label="다운로드"></Button>
                        </div>
                    </div>
                </div>
                <div class="col-12 md:col-3"></div>
            </div>
            <div class="grid p-fluid w-100">
                <div class="col-12 md:col-3"></div>
                <div class="col-12 md:col-3">
                    <Card>
                        <template #title>
                            <div class="w-100 flex justify-content-between">
                                <span>구간 세부 설정</span>
                            </div>
                        </template>
                        <template #content>
                            <div class="w-100 flex">
                                <div class="grid p-fluid w-100">
                                    <div class="col-12 md:col-3 flex align-items-center">
                                        <span class="video-length">재생지점</span>
                                    </div>
                                    <div class="col-12 md:col-6">
                                        <InputText v-model="this.currentTime"/>
                                    </div>
                                    <div class="col-12 md:col-3"></div>
                                    
                                    <div class="col-12 md:col-3 flex align-items-center">
                                        <span class="video-length">시작 점</span>
                                    </div>
                                    <div class="col-12 md:col-6">
                                        <InputText v-model="this.trim.start"/>
                                    </div>
                                    <div class="col-12 md:col-3">
                                        <Button class="p-button-raised p-button-rounded" label="재생" v-on:click="this.trimStartPointPlay"/>
                                    </div>
                                    <div class="col-12 md:col-3 flex align-items-center">
                                        <span class="video-length">종료 점</span>
                                    </div>
                                    <div class="col-12 md:col-6">
                                        <InputText v-model="this.trim.end"/>
                                    </div>
                                    <div class="col-12 md:col-3">
                                        <Button class="p-button-raised p-button-rounded" label="재생" v-on:click="this.trimEndPointPlay"/>
                                    </div>
                                </div>
                            </div>
                        </template>
                    </Card>
                </div>
                <div class="col-12 md:col-3">
                    <Card>
                        <template #title>
                            <div class="w-100 flex justify-content-between">
                                <span>Youtube에 업로드</span>
                            </div>
                        </template>
                        <template #content>
                            <div class="w-100 flex">
                                <div class="grid p-fluid w-100">
                                    <div class="col-12 md:col-3 flex align-items-center">
                                        <span class="video-length">종료 점</span>
                                    </div>
                                    <div class="col-12 md:col-6">
                                        <InputText v-model="this.trim.end"/>
                                    </div>
                                    <div class="col-12 md:col-3">
                                        <Button class="p-button-raised p-button-rounded" label="재생" v-on:click="this.trimEndPointPlay"/>
                                    </div>
                                </div>
                            </div>
                        </template>
                    </Card>
                </div>
                <div class="col-12 md:col-3"></div>
            </div>
        </div>
        <div class="black-panel"></div>
    </div>
</template>

<script>
import VideoPlayer from '@/components/Video.vue';
export default {
    components:{
        VideoPlayer
    },
    data(){
        return{
            video_source: 'https://vjs.zencdn.net/v/oceans.mp4',
            video_type: 'video/mp4',
            video_info:{
                title: '',
                url: '',
                length: '',
                time_info: [],
            },
            vStreams: [],
            currentTime: 0,
            trim:{
                start: '00:00:00',
                end: '00:00:00',
            },
            downloadModalVisible: false,
            selectedVideoType: '',

        }
    },
    methods:{
        openDownloadModal() {
            this.downloadModalVisible = true;
        },
        closeDownloadModal() {
            this.downloadModalVisible = false;
        },
        timeStringToTimestamp(s){
            let time = s;
            let array = time.split(":");
            let timestamp = (parseInt(array[0], 10) * 60 * 60) + (parseInt(array[1], 10) * 60) + parseFloat(array[2]);
            return timestamp
        },
        timestampToTime(ts){
            return new Date(ts * 1000).toISOString().slice(11, 23);
        },
        playVideo(){
            this.$refs.player.player.play();
        },
        trimStartPointPlay(){
            let ts = this.timeStringToTimestamp(this.trim.start);
            this.$refs.player.setCurrentTime(ts)
            this.playVideo();
        },
        trimEndPointPlay(){
            let ts = this.timeStringToTimestamp(this.trim.end);
            this.$refs.player.setCurrentTime(ts)
            this.playVideo();
        },
        setupVideoPlayer(url, type){
            this.$refs.player.setVideoPlayer(url, type);
            this.trim.start = this.timestampToTime(0);
            this.$refs.player.addVideoEventListener("loadedmetadata", () => {
                this.trim.end = this.timestampToTime(this.$refs.player.videoElem.duration);
                this.video_info.length = this.trim.end;
            });
            this.$refs.player.addVideoEventListener("timeupdate", () => {
                this.currentTime = this.timestampToTime(this.$refs.player.getCurrentTime());
            });
        },
        async initVideoPlayer(){
            let resp = await fetch(this.url + "/vidinfo");
            if(resp.status === 200){
                let json = await resp.json();
                this.video_info.time_info = json.time_info;
                this.video_info.length = json['length'];
                this.video_info.title = json.title;
                this.vStreams = json.streams;
                this.video_source = this.vStreams[this.vStreams.length-1].url;
                this.video_type = this.vStreams[this.vStreams.length-1].mime_type;
                this.setupVideoPlayer(this.video_source, this.video_type);
            }
            else{
                alert('비디오 정보 조회에 실패했습니다.');
                throw new Error('fail to get video information')
            }
        }
    },
    computed: {
        
    },
    async mounted(){
        this.setupVideoPlayer(this.video_source, this.video_type);
        // this.initVideoPlayer();
    }
    
}
</script>
<style scoped lang="scss">
@import "../assets/css/main.css";
@import url('https://fonts.googleapis.com/css2?family=Heebo&family=Poppins:wght@300&family=Rubik&display=swap');

@media only screen and (max-width: 440px) {
    .main-view { 
        padding: .5rem .7rem !important;
    }
    .border-box span{
        font-size: 1rem !important;
    }
}
//override
.grid {
    margin: 0px;
}
.red-panel{
    background-color: rgb(254, 114, 114);
    width: 100vw;
    height: 60px;
}
.black-panel{
    background-color: rgb(92, 92, 92);
    width: 100vw;
    height: 60px;
}
.main-view{
    padding: 3rem 5rem;
    height: calc(100vh - 120px);
}
.video-layout{
    max-width: 100%;
    min-width: 70%;
    max-height: 100%;
    
    border-radius: 20px;
    overflow: hidden;
}

.video-info{
    text-align: left;
    font-family: 'Heebo', sans-serif;
    margin: 0;
    color: black;
    font-weight: 600;
}

.video-title{
    font-size: 1.7rem;
}

.video-url{
    font-size: .9rem;
    color: rgb(44, 125, 255);
}

.video-length{
    display: flex;
    align-items: center;
    font-size: 1.2rem;
    color: #626262;
}

.card-header{
    text-align: left;
    font-family: 'Heebo', sans-serif;
    margin: 0px 0px 0.2rem 0px;
    color: rgb(254, 114, 114);
    font-weight: 600;
    font-size: 1.5rem;
    padding: 0;
}

.border-box{
    border: 0.1rem solid rgb(134, 134, 134);
    border-radius: 10px;
    overflow: hidden;
    display: flex;
    justify-content: center;
}

.border-box span{
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
}

.border-box button{
    border-top-left-radius: 0px !important;
    border-bottom-left-radius: 0px !important;
}

//override
.p-card{
    border-radius: 0px !important;
}

.btn-sm-red{
    width: 11rem !important;
    background-color: rgb(254, 114, 114);
    border: 0.1rem solid rgb(255, 119, 119);
}

.btn-red{
    background-color: rgb(254, 114, 114) !important;
    border: 0.1rem solid rgb(255, 119, 119) !important;
}

</style>
<style>
.p-dialog{
    border: 0.12rem solid rgb(134, 134, 134);
    box-shadow: none;
}

.p-dialog .p-dialog-header{
    color: rgb(254, 114, 114) !important;
}

.p-dialog .p-dialog-header .p-dialog-header-icon{
    display: none;
}

.video-js.vjs-fluid:not(.vjs-audio-only-mode) {
    height: none;
}

</style>